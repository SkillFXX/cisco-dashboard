import datetime
import json
import logging
import threading
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import requests
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..mailer import load_smtp, is_configured, send_mail
from ..models import (
    User, PersonalTask, CompletedExternalTask,
    NotificationRule, NotificationLog, NotificationChannels,
)
from .ical_service import fetch_timetable
from .moodle_service import fetch_moodle_data
from .scodoc_service import fetch_scodoc_data
from .url_guard import validate_service_url

logger = logging.getLogger(__name__)

PARIS = ZoneInfo("Europe/Paris")
UTC = datetime.timezone.utc
CYCLE_SECONDS = 300
CATEGORY_LABELS = {"ds": "DS", "dm": "DM", "tp": "TP", "other": "Autre"}


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(UTC).replace(tzinfo=None)


def _local_naive_to_utc(dt: datetime.datetime) -> datetime.datetime:
    """Datetime naif en heure du serveur -> UTC naif."""
    return dt.astimezone(UTC).replace(tzinfo=None)


def _paris_naive_to_utc(dt: datetime.datetime) -> datetime.datetime:
    return dt.replace(tzinfo=PARIS).astimezone(UTC).replace(tzinfo=None)


def format_paris(dt_utc: datetime.datetime) -> str:
    local = dt_utc.replace(tzinfo=UTC).astimezone(PARIS)
    return local.strftime("%d/%m/%Y à %H:%M")


# ---------------------------------------------------------------- Envoi

def send_to_channels(db: Session, user: User, channels: List[str], subject: str, body: str) -> List[str]:
    """Envoie sur les canaux demandes. Retourne la liste des erreurs (vide si tout est parti)."""
    errors: List[str] = []
    if "email" in channels:
        try:
            send_mail(user.email, subject, body)
        except Exception as e:
            errors.append(f"email: {e}")
    if "webhook" in channels:
        row = db.get(NotificationChannels, user.id)
        url = row.webhook_url if row else None
        if not url:
            errors.append("webhook: aucune URL configurée")
        else:
            err = validate_service_url(url)
            if err:
                errors.append(f"webhook: {err}")
            else:
                try:
                    text = f"**{subject}**\n{body}"[:1900]
                    resp = requests.post(url, json={"content": text, "text": text}, timeout=10, allow_redirects=False)
                    if resp.status_code >= 300:
                        errors.append(f"webhook: HTTP {resp.status_code}")
                except Exception as e:
                    errors.append(f"webhook: {e}")
    return errors


# ------------------------------------------------------------ Collecte

def collect_deadlines(db: Session, user: User) -> List[Dict[str, Any]]:
    """Devoirs/DS de l'utilisateur (faits ou non), echeances en UTC naif."""
    items: List[Dict[str, Any]] = []
    completed = {r.item_id for r in db.query(CompletedExternalTask).filter(CompletedExternalTask.user_id == user.id)}

    for t in db.query(PersonalTask).filter(PersonalTask.user_id == user.id):
        cat = t.event_type if t.event_type in ("ds", "dm", "tp") else "other"
        items.append({
            "key": f"personal-{t.id}", "title": t.title, "subject": t.subject or "",
            "category": cat, "due": t.due_date, "done": t.status == "done",
        })

    creds = user.credentials
    if creds and creds.moodle_url:
        try:
            data = fetch_moodle_data(
                url=creds.moodle_url, username=creds.moodle_username, password=creds.moodle_password, token=creds.moodle_token,
            )
            for m in data.get("upcoming_assignments", []):
                key = f"moodle-{m['id']}"
                items.append({
                    "key": key, "title": m["name"], "subject": m.get("course_name", ""), "category": "dm",
                    "due": _local_naive_to_utc(datetime.datetime.fromisoformat(m["duedate"])), "done": key in completed,
                })
        except Exception as e:
            logger.debug(f"Notifications: Moodle indisponible pour {user.id}: {e}")

    if creds and creds.ical_url:
        try:
            data = fetch_timetable(ical_url=creds.ical_url)
            for ev in data.get("all_events", []):
                if ev.get("type") != "DS":
                    continue
                key = f"timetable-{ev.get('id') or ev['dt_start']}"
                items.append({
                    "key": key, "title": ev.get("title", "Contrôle DS"), "subject": "", "category": "ds",
                    "due": _paris_naive_to_utc(datetime.datetime.fromisoformat(ev["dt_start"])), "done": key in completed,
                })
        except Exception as e:
            logger.debug(f"Notifications: emploi du temps indisponible pour {user.id}: {e}")
    return items


def collect_grades(user: User) -> Optional[List[Dict[str, Any]]]:
    """Toutes les notes connues (None si ScoDoc est indisponible)."""
    creds = user.credentials
    if not creds or not creds.scodoc_username or not creds.scodoc_password:
        return None
    data = fetch_scodoc_data(
        user_id=user.id, url=creds.scodoc_url, username=creds.scodoc_username, password=creds.scodoc_password,
    )
    if not data.get("configured") or data.get("connection_error"):
        return None
    grades = []
    for mat in data.get("matieres", []):
        for ev in mat.get("evaluations", []):
            if ev.get("note") is not None and ev.get("id") is not None:
                grades.append({
                    "key": f"grade:{ev['id']}", "matiere": f"{mat.get('code', '')} {mat.get('titre', '')}".strip(),
                    "description": ev.get("description") or "Évaluation", "note": ev["note"], "moy_promo": ev.get("moy_promo"),
                })
    return grades


# ----------------------------------------------------------- Evaluation

def _claim(db: Session, user_id: int, rule_id: int, key: str) -> bool:
    """Reserve une notification (anti-doublon). False si deja envoyee."""
    db.add(NotificationLog(user_id=user_id, rule_id=rule_id, dedupe_key=key))
    try:
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False


def _release(db: Session, rule_id: int, key: str) -> None:
    db.query(NotificationLog).filter(NotificationLog.rule_id == rule_id, NotificationLog.dedupe_key == key).delete()
    db.commit()


def _deliver(db: Session, user: User, rule: NotificationRule, key: str, subject: str, body: str) -> None:
    if not _claim(db, user.id, rule.id, key):
        return
    errors = send_to_channels(db, user, json.loads(rule.channels or "[]"), subject, body)
    if errors:
        logger.warning(f"Notification '{rule.name}' (user {user.id}) en échec : {errors}")
        _release(db, rule.id, key)  # sera retentee au prochain cycle


def _run_new_grade(db: Session, user: User, rule: NotificationRule, grades: Optional[List[Dict[str, Any]]]) -> None:
    if grades is None:
        return
    if not rule.baseline_done:
        # Premier passage : memoriser les notes existantes sans notifier
        for g in grades:
            _claim(db, user.id, rule.id, g["key"])
        rule.baseline_done = True
        db.commit()
        return
    for g in grades:
        moy = f" (moyenne de promo : {g['moy_promo']})" if g.get("moy_promo") is not None else ""
        _deliver(db, user, rule, g["key"], "Nouvelle note disponible",
                 f"{g['matiere']} — {g['description']} : {g['note']}/20{moy}")


def _run_deadline(db: Session, user: User, rule: NotificationRule, params: Dict[str, Any], items: List[Dict[str, Any]], now: datetime.datetime) -> None:
    hours = int(params.get("hours_before", 24))
    include_done = bool(params.get("include_done", False))
    categories = params.get("categories") or []
    window = datetime.timedelta(hours=hours)
    for it in items:
        if it["done"] and not include_done:
            continue
        if categories and it["category"] not in categories:
            continue
        if not (it["due"] - window <= now < it["due"]):
            continue
        status = "déjà fait" if it["done"] else "à faire"
        subject_part = f" ({it['subject']})" if it["subject"] else ""
        _deliver(db, user, rule, f"deadline:{it['key']}:{it['due'].isoformat()}",
                 f"{CATEGORY_LABELS[it['category']]} à rendre bientôt",
                 f"{it['title']}{subject_part} — échéance le {format_paris(it['due'])} ({status})")


def _run_digest(db: Session, user: User, rule: NotificationRule, params: Dict[str, Any], items: List[Dict[str, Any]], now: datetime.datetime) -> None:
    now_paris = now.replace(tzinfo=UTC).astimezone(PARIS)
    if now_paris.hour < int(params.get("hour", 18)):
        return
    days = int(params.get("days_ahead", 3))
    include_done = bool(params.get("include_done", False))
    upcoming = sorted(
        (i for i in items if now <= i["due"] <= now + datetime.timedelta(days=days) and (include_done or not i["done"])),
        key=lambda i: i["due"],
    )
    if not upcoming:
        return
    lines = [f"- {i['title']} — {format_paris(i['due'])}" + (" ✔" if i["done"] else "") for i in upcoming[:15]]
    _deliver(db, user, rule, f"digest:{now_paris.date().isoformat()}",
             f"Récapitulatif : {len(upcoming)} échéance(s) dans les {days} prochains jours", "\n".join(lines))


def run_rules_for_user(db: Session, user: User, rules: List[NotificationRule]) -> None:
    now = _utcnow()
    triggers = {r.trigger for r in rules}
    grades = collect_grades(user) if "new_grade" in triggers else None
    items = collect_deadlines(db, user) if triggers & {"deadline", "daily_digest"} else []
    for rule in rules:
        try:
            params = json.loads(rule.params or "{}")
            if rule.trigger == "new_grade":
                _run_new_grade(db, user, rule, grades)
            elif rule.trigger == "deadline":
                _run_deadline(db, user, rule, params, items, now)
            elif rule.trigger == "daily_digest":
                _run_digest(db, user, rule, params, items, now)
        except Exception as e:
            db.rollback()
            logger.warning(f"Règle de notification {rule.id} ignorée : {e}")


def run_notification_cycle() -> None:
    db = SessionLocal()
    try:
        rules = db.query(NotificationRule).filter(NotificationRule.enabled == True).all()  # noqa: E712
        by_user: Dict[int, List[NotificationRule]] = {}
        for r in rules:
            by_user.setdefault(r.user_id, []).append(r)
        for user_id, user_rules in by_user.items():
            user = db.get(User, user_id)
            if user:
                run_rules_for_user(db, user, user_rules)
        # Nettoyage des journaux anciens (conserve 60 jours)
        db.query(NotificationLog).filter(NotificationLog.sent_at < _utcnow() - datetime.timedelta(days=60)).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Cycle de notifications en échec : {e}")
    finally:
        db.close()


_stop = threading.Event()


def _loop() -> None:
    _stop.wait(30)  # laisse l'application demarrer
    while not _stop.is_set():
        run_notification_cycle()
        _stop.wait(CYCLE_SECONDS)


def start_scheduler() -> threading.Thread:
    thread = threading.Thread(target=_loop, name="notification-scheduler", daemon=True)
    thread.start()
    return thread


def stop_scheduler() -> None:
    _stop.set()
