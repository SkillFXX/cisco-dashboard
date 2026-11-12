import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

API_BASE = os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta")
DEFAULT_MODEL = "gemini-2.5-flash-lite"
MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
# Caractères ASCII visibles uniquement (les clés Google peuvent contenir « . » ou d'autres symboles) : sans espaces ni retours à la ligne, pour rester sûr dans un en-tête HTTP
KEY_RE = re.compile(r"^[\x21-\x7e]{20,200}$")

MAX_OUTPUT_TOKENS = 600
MAX_HISTORY_MESSAGES = 6
MAX_MESSAGE_CHARS = 600

SYSTEM_PROMPT = (
    "Tu es l'assistant du tableau de bord d'un étudiant en BUT. "
    "Réponds en français, de façon courte et précise (quelques lignes, listes à puces si utile), "
    "uniquement à partir des données ci-dessous. Si une information manque, dis-le sans rien inventer. "
    "Pour un calcul de moyenne, montre la formule en une ligne.\n\nDONNÉES:\n"
)


class GeminiError(Exception):
    def __init__(self, message: str, status: int = 502, invalid_key: bool = False):
        super().__init__(message)
        self.message = message
        self.status = status
        self.invalid_key = invalid_key


def _generate(api_key: str, model: str, system: str, contents: List[Dict[str, Any]], max_tokens: int, tools: Optional[List[Dict[str, Any]]] = None) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
    config: Dict[str, Any] = {"maxOutputTokens": max_tokens, "temperature": 0.3}
    # Les modèles 2.5 "flash" réfléchissent par défaut : ces tokens de réflexion consomment le quota et la limite de sortie.
    if "2.5-flash" in model:
        config["thinkingConfig"] = {"thinkingBudget": 0}
    body: Dict[str, Any] = {"contents": contents, "generationConfig": config}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    if tools:
        body["tools"] = tools

    url = f"{API_BASE}/models/{model}:generateContent"
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    try:
        resp = requests.post(url, json=body, headers=headers, timeout=45)
        if resp.status_code == 400 and "thinking" in resp.text.lower():
            config.pop("thinkingConfig", None)
            resp = requests.post(url, json=body, headers=headers, timeout=45)
    except requests.RequestException as e:
        raise GeminiError(f"Impossible de joindre l'API Gemini : {e.__class__.__name__}.") from e

    if resp.status_code != 200:
        try:
            err = resp.json().get("error", {})
        except ValueError:
            err = {}
        message = err.get("message") or f"HTTP {resp.status_code}"
        low = message.lower()
        if resp.status_code in (400, 401, 403) and ("api key" in low or "api_key" in low or "permission" in low):
            raise GeminiError("Clé d'API Gemini refusée. Vérifiez-la dans Google AI Studio.", 400, invalid_key=True)
        if resp.status_code == 404:
            raise GeminiError(f"Modèle « {model} » introuvable pour cette clé.", 400)
        if resp.status_code == 429:
            raise GeminiError("Quota gratuit Gemini atteint. Réessayez dans un instant.", 429)
        raise GeminiError(f"Erreur Gemini : {message[:200]}", 502)

    data = resp.json()
    candidates = data.get("candidates") or []
    parts = (candidates[0].get("content", {}).get("parts") if candidates else None) or []
    text = "".join(p.get("text", "") for p in parts).strip()
    calls = [p["functionCall"] for p in parts if p.get("functionCall")]
    usage = data.get("usageMetadata", {})
    if not text and not calls:
        reason = candidates[0].get("finishReason") if candidates else (data.get("promptFeedback", {}) or {}).get("blockReason")
        raise GeminiError(f"Aucune réponse générée ({reason or 'vide'}). Reformulez la question.", 502)
    return text, usage, calls


def verify_key(api_key: str, model: str) -> None:
    """Appel minimal (quelques tokens) pour s'assurer que la clé et le modèle fonctionnent."""
    _generate(api_key, model, "", [{"role": "user", "parts": [{"text": "Réponds uniquement : OK"}]}], 16)


ADD_HOMEWORK_TOOL = [{
    "functionDeclarations": [{
        "name": "add_homework",
        "description": "Ajoute un devoir / DS / rappel à la liste de l'étudiant. À appeler seulement quand l'étudiant le demande explicitement.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Titre court du devoir"},
                "due_date": {"type": "string", "description": "Échéance, heure de Paris, format AAAA-MM-JJ HH:MM. Sans heure précisée : 08:00. Calcule les dates relatives (demain, vendredi prochain) à partir de « Maintenant »."},
                "category": {"type": "string", "enum": ["ds", "dm", "tp", "todo"], "description": "ds = contrôle, dm = devoir maison, tp = TP à rendre, todo = autre"},
                "subject": {"type": "string", "description": "Matière, idéalement un élément de la liste MATIÈRES (code + nom)"},
                "description": {"type": "string", "description": "Consignes ou notes (facultatif)"},
            },
            "required": ["title", "due_date"],
        },
    }]
}]


def chat(api_key: str, model: str, context: str, messages: List[Dict[str, str]], allow_actions: bool = False) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
    history = messages[-MAX_HISTORY_MESSAGES:]
    contents = [
        {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"][:MAX_MESSAGE_CHARS]}]}
        for m in history
    ]
    # Gemini exige que la conversation commence par un message utilisateur
    while contents and contents[0]["role"] != "user":
        contents.pop(0)
    return _generate(api_key, model, SYSTEM_PROMPT + context, contents, MAX_OUTPUT_TOKENS, ADD_HOMEWORK_TOOL if allow_actions else None)
