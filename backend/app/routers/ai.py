import logging
from typing import List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..database import get_db
import datetime
from zoneinfo import ZoneInfo
from ..models import User, AiSettings, PersonalTask
from ..auth import get_current_user
from ..ratelimit import ai_minute_limiter, ai_day_limiter
from ..services import gemini
from ..services.ai_context import build_context, wants_action, DAYS_LONG

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["ai"])


class VerifyIn(BaseModel):
    api_key: Optional[str] = Field(default=None, max_length=200)
    model: Optional[str] = Field(default=None, max_length=80)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatIn(BaseModel):
    messages: List[ChatMessage] = Field(min_length=1, max_length=50)


def _status(row: Optional[AiSettings]) -> dict:
    key = row.api_key if row else None
    return {
        "configured": bool(key),
        "verified": bool(row and key and row.verified),
        "model": row.model if row else gemini.DEFAULT_MODEL,
        "key_hint": f"…{key[-4:]}" if key else None,
        "last_error": row.last_error if row else None,
    }


PARIS = ZoneInfo("Europe/Paris")
UTC = datetime.timezone.utc
CATEGORIES = {"ds", "dm", "tp", "todo"}
MAX_ACTIONS = 3


def _create_homework(db: Session, user: User, args: dict) -> str:
    """Execute l'outil add_homework demandé par le modèle. Retourne une phrase de confirmation, ou lève ValueError."""
    title = str(args.get("title") or "").strip()[:200]
    if not title:
        raise ValueError("titre manquant")
    raw_due = str(args.get("due_date") or "").strip().replace("T", " ")
    try:
        due_local = datetime.datetime.strptime(raw_due[:16], "%Y-%m-%d %H:%M")
    except ValueError:
        raise ValueError(f"date d'échéance illisible ({raw_due or 'vide'})")
    now_local = datetime.datetime.now(PARIS).replace(tzinfo=None)
    if not (now_local - datetime.timedelta(days=1) <= due_local <= now_local + datetime.timedelta(days=730)):
        raise ValueError("date d'échéance hors limites")
    category = args.get("category") if args.get("category") in CATEGORIES else "todo"
    subject = (str(args.get("subject") or "").strip()[:100]) or None
    description = (str(args.get("description") or "").strip()[:2000]) or None

    task = PersonalTask(
        user_id=user.id, title=title, subject=subject, description=description, event_type=category, status="todo",
        due_date=due_local.replace(tzinfo=PARIS).astimezone(UTC).replace(tzinfo=None),  # stocké en UTC, comme depuis l'interface
    )
    db.add(task)
    db.commit()
    when = f"{DAYS_LONG[due_local.weekday()]} {due_local.strftime('%d/%m à %H:%M')}"
    return f"Devoir ajouté : **{title}**" + (f" ({subject})" if subject else "") + f", pour le {when}."


@router.get("")
def get_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _status(db.get(AiSettings, current_user.id))


@router.post("/verify")
def verify(payload: VerifyIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Teste la clé (nouvelle ou déjà enregistrée) ; l'enregistre si elle fonctionne."""
    ai_minute_limiter.check(f"verify:{current_user.id}")
    ai_minute_limiter.record(f"verify:{current_user.id}")
    row = db.get(AiSettings, current_user.id)

    model = (payload.model or (row.model if row else None) or gemini.DEFAULT_MODEL).strip()
    if not gemini.MODEL_RE.match(model):
        raise HTTPException(status_code=400, detail="Nom de modèle invalide.")
    key = (payload.api_key or "").strip() or (row.api_key if row else None)
    if not key:
        raise HTTPException(status_code=400, detail="Renseignez une clé d'API Gemini.")
    if not gemini.KEY_RE.match(key):
        raise HTTPException(status_code=400, detail="Format de clé invalide (lettres, chiffres, - et _ uniquement).")

    try:
        gemini.verify_key(key, model)
    except gemini.GeminiError as e:
        if row:
            row.verified = False
            row.last_error = e.message[:300]
            db.commit()
        raise HTTPException(status_code=e.status if e.status in (400, 429) else 502, detail=e.message)

    if not row:
        row = AiSettings(user_id=current_user.id)
        db.add(row)
    row.api_key, row.model, row.verified, row.last_error = key, model, True, None
    db.commit()
    return _status(row)


@router.delete("")
def remove(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.get(AiSettings, current_user.id)
    if row:
        db.delete(row)
        db.commit()
    return _status(None)


@router.post("/chat")
def chat(payload: ChatIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.get(AiSettings, current_user.id)
    if not row or not row.api_key or not row.verified:
        raise HTTPException(status_code=400, detail="L'assistant IA n'est pas configuré.")
    if payload.messages[-1].role != "user":
        raise HTTPException(status_code=400, detail="Le dernier message doit venir de l'utilisateur.")

    ai_minute_limiter.check(f"chat:{current_user.id}")
    ai_day_limiter.check(f"chat:{current_user.id}")
    ai_minute_limiter.record(f"chat:{current_user.id}")
    ai_day_limiter.record(f"chat:{current_user.id}")

    messages = [{"role": m.role, "content": m.content} for m in payload.messages]
    # Rubriques choisies d'après la question et la précédente (pour les relances « et demain ? »)
    user_texts = [m["content"] for m in messages if m["role"] == "user"][-2:]
    allow_actions = wants_action(user_texts)
    context = build_context(db, current_user, user_texts, with_subjects=allow_actions)

    try:
        reply, usage, calls = gemini.chat(row.api_key, row.model, context, messages, allow_actions)
    except gemini.GeminiError as e:
        if e.invalid_key:
            row.verified = False
            row.last_error = e.message
            db.commit()
        raise HTTPException(status_code=e.status if e.status in (400, 429) else 502, detail=e.message)

    created = 0
    notes: List[str] = []
    for call in calls[:MAX_ACTIONS] if allow_actions else []:
        if call.get("name") != "add_homework":
            continue
        try:
            notes.append(_create_homework(db, current_user, call.get("args") or {}))
            created += 1
        except ValueError as e:
            db.rollback()
            notes.append(f"Je n'ai pas pu ajouter ce devoir : {e}.")
    if notes:
        reply = "\n".join(([reply] if reply else []) + [f"- {n}" for n in notes]) if len(notes) > 1 else "\n".join(([reply] if reply else []) + notes)

    logger.info(f"IA user {current_user.id}: {usage.get('promptTokenCount')} tokens entrée, {usage.get('candidatesTokenCount')} sortie")
    return {
        "reply": reply,
        "usage": {"prompt": usage.get("promptTokenCount"), "output": usage.get("candidatesTokenCount")},
        "tasks_created": created,
    }
