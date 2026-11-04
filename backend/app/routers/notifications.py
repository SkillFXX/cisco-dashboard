import json
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, NotificationRule, NotificationChannels, NotificationLog
from ..auth import get_current_user, require_admin
from ..mailer import load_smtp, is_configured
from ..services.notifier import send_to_channels
from ..services.url_guard import validate_service_url

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

MAX_RULES_PER_USER = 20
Channel = Literal["email", "webhook"]


class RuleIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    enabled: bool = True
    trigger: Literal["new_grade", "deadline", "daily_digest"]
    params: Dict[str, Any] = {}
    channels: List[Channel] = Field(min_length=1)


class ChannelsIn(BaseModel):
    webhook_url: Optional[str] = Field(default=None, max_length=512)


class TestIn(BaseModel):
    channel: Channel


def _clamp(value: Any, low: int, high: int, default: int) -> int:
    try:
        return max(low, min(high, int(value)))
    except (TypeError, ValueError):
        return default


def _normalize_params(trigger: str, params: Dict[str, Any]) -> Dict[str, Any]:
    if trigger == "deadline":
        cats = [c for c in (params.get("categories") or []) if c in ("ds", "dm", "tp", "other")]
        return {
            "hours_before": _clamp(params.get("hours_before"), 1, 24 * 30, 24),
            "include_done": bool(params.get("include_done", False)),
            "categories": cats,
        }
    if trigger == "daily_digest":
        return {
            "hour": _clamp(params.get("hour"), 0, 23, 18),
            "days_ahead": _clamp(params.get("days_ahead"), 1, 14, 3),
            "include_done": bool(params.get("include_done", False)),
        }
    return {}


def _serialize_rule(r: NotificationRule) -> dict:
    return {
        "id": r.id, "name": r.name, "enabled": bool(r.enabled), "trigger": r.trigger,
        "params": json.loads(r.params or "{}"), "channels": json.loads(r.channels or "[]"),
    }


def _mask(url: Optional[str]) -> Optional[str]:
    """N'expose que l'hote : le jeton du webhook reste secret."""
    if not url:
        return None
    from urllib.parse import urlparse
    return f"{urlparse(url).hostname or 'webhook'}/…"


def _get_rule(db: Session, user: User, rule_id: int) -> NotificationRule:
    rule = db.query(NotificationRule).filter(NotificationRule.id == rule_id, NotificationRule.user_id == user.id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Notification introuvable.")
    return rule


@router.get("")
def get_overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    channels = db.get(NotificationChannels, current_user.id)
    rules = db.query(NotificationRule).filter(NotificationRule.user_id == current_user.id).order_by(NotificationRule.id).all()
    return {
        "email_available": is_configured(load_smtp(db)),
        "email_address": current_user.email,
        "webhook_configured": bool(channels and channels.webhook_url),
        "webhook_masked": _mask(channels.webhook_url if channels else None),
        "rules": [_serialize_rule(r) for r in rules],
    }


@router.put("/channels")
def update_channels(payload: ChannelsIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    url = (payload.webhook_url or "").strip()
    if url:
        if not url.startswith("https://"):
            raise HTTPException(status_code=400, detail="L'URL du webhook doit commencer par https://")
        err = validate_service_url(url)
        if err:
            raise HTTPException(status_code=400, detail=err)
    row = db.get(NotificationChannels, current_user.id)
    if not row:
        row = NotificationChannels(user_id=current_user.id)
        db.add(row)
    row.webhook_url = url or None
    db.commit()
    return {"webhook_configured": bool(url), "webhook_masked": _mask(url)}


@router.post("/rules", status_code=status.HTTP_201_CREATED)
def create_rule(payload: RuleIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    count = db.query(NotificationRule).filter(NotificationRule.user_id == current_user.id).count()
    if count >= MAX_RULES_PER_USER:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_RULES_PER_USER} notifications.")
    rule = NotificationRule(
        user_id=current_user.id, name=payload.name.strip(), enabled=payload.enabled, trigger=payload.trigger,
        params=json.dumps(_normalize_params(payload.trigger, payload.params)), channels=json.dumps(sorted(set(payload.channels))),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return _serialize_rule(rule)


@router.put("/rules/{rule_id}")
def update_rule(rule_id: int, payload: RuleIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rule = _get_rule(db, current_user, rule_id)
    if rule.trigger != payload.trigger:
        # Un nouveau declencheur repart d'une base propre
        db.query(NotificationLog).filter(NotificationLog.rule_id == rule.id).delete()
        rule.baseline_done = False
    rule.name = payload.name.strip()
    rule.enabled = payload.enabled
    rule.trigger = payload.trigger
    rule.params = json.dumps(_normalize_params(payload.trigger, payload.params))
    rule.channels = json.dumps(sorted(set(payload.channels)))
    db.commit()
    db.refresh(rule)
    return _serialize_rule(rule)


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rule = _get_rule(db, current_user, rule_id)
    db.query(NotificationLog).filter(NotificationLog.rule_id == rule.id).delete()
    db.delete(rule)
    db.commit()
    return None


@router.post("/test")
def send_test(payload: TestIn, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    errors = send_to_channels(db, current_user, [payload.channel], "Notification de test", "Si vous voyez ce message, ce canal fonctionne.")
    if errors:
        raise HTTPException(status_code=400, detail=f"Échec de l'envoi : {errors[0]}")
    return {"success": True}
