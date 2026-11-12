import logging
import os
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

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
    "Réponds dans la langue de l'étudiant, de façon courte et précise (quelques lignes, listes à puces si utile), "
    "uniquement à partir des données ci-dessous et des outils. Si une information manque, dis-le sans rien inventer. "
    "Pour un calcul de moyenne, montre la formule en une ligne.\n"
    "Les données ci-dessous sont un résumé : pour le détail (notes, absences, emploi du temps plus lointain, "
    "documents Moodle d'un cours), appelle l'outil adapté. N'appelle add_homework que sur demande explicite d'ajout.\n\nDONNÉES:\n"
)

# Variante pour les modeles sans appel d'outils : toutes les donnees sont deja dans le contexte
SYSTEM_PROMPT_NO_TOOLS = (
    "Tu es l'assistant du tableau de bord d'un étudiant en BUT. "
    "Réponds dans la langue de l'étudiant, de façon courte et précise (quelques lignes, listes à puces si utile), "
    "uniquement à partir des données ci-dessous. Si une information manque, dis-le sans rien inventer. "
    "Pour un calcul de moyenne, montre la formule en une ligne. "
    "Tu ne peux pas modifier les données : pour ajouter un devoir, indique d'utiliser le bouton « Nouveau DS / Devoir ».\n\nDONNÉES:\n"
)

MAX_TOOL_ROUNDS = 3
# Modeles dont l'API a deja refuse les outils (ex. Gemma) : on ne reessaie pas a chaque message
_NO_TOOLS_MODELS: set = set()


class GeminiError(Exception):
    def __init__(self, message: str, status: int = 502, invalid_key: bool = False, tools_unsupported: bool = False):
        super().__init__(message)
        self.message = message
        self.status = status
        self.invalid_key = invalid_key
        self.tools_unsupported = tools_unsupported


def _generate(api_key: str, model: str, system: str, contents: List[Dict[str, Any]], max_tokens: int, tools: Optional[List[Dict[str, Any]]] = None) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
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
        if resp.status_code == 400 and tools and ("function" in low or "tool" in low) and any(w in low for w in ("not enabled", "not supported", "unsupported", "invalid")):
            raise GeminiError("Ce modèle ne gère pas les outils.", 400, tools_unsupported=True)
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
    return text, usage, calls, parts


def verify_key(api_key: str, model: str) -> None:
    """Appel minimal (quelques tokens) pour s'assurer que la clé et le modèle fonctionnent."""
    _generate(api_key, model, "", [{"role": "user", "parts": [{"text": "Réponds uniquement : OK"}]}], 16)


# Outils de lecture : le modele les appelle pour obtenir le detail (executes par ai_context.run_read_tool)
READ_TOOLS_DECL = [{
    "functionDeclarations": [
        {
            "name": "get_grades",
            "description": "Notes détaillées : moyennes par UE et par matière, dernières évaluations avec moyennes de la promo.",
        },
        {
            "name": "get_absences",
            "description": "Bilan des absences et retards, avec les derniers créneaux.",
        },
        {
            "name": "get_timetable",
            "description": "Emploi du temps (cours, salles, enseignants) des prochains jours, à partir d'aujourd'hui.",
            "parameters": {
                "type": "object",
                "properties": {"days": {"type": "integer", "description": "Nombre de jours à couvrir, de 1 à 21 (7 par défaut)"}},
            },
        },
        {
            "name": "list_course_documents",
            "description": "Noms des documents Moodle (supports, TP, sujets...) d'un cours. Le contenu des fichiers n'est pas lisible.",
            "parameters": {
                "type": "object",
                "properties": {"course": {"type": "string", "description": "Code ou nom du cours, ex. R101"}},
                "required": ["course"],
            },
        },
    ]
}]
READ_TOOL_NAMES_SET = {d["name"] for d in READ_TOOLS_DECL[0]["functionDeclarations"]}

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


def _add_usage(total: Dict[str, int], usage: Dict[str, Any]) -> None:
    for key in ("promptTokenCount", "candidatesTokenCount"):
        total[key] = total.get(key, 0) + int(usage.get(key) or 0)


def chat(
    api_key: str,
    model: str,
    context: str,
    messages: List[Dict[str, str]],
    run_tool: Callable[[str, Dict[str, Any]], str],
    full_context: Callable[[], str],
) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
    """Conversation avec outils : le modele demande lui-meme les donnees de detail (boucle limitee).

    Retourne (texte, usage cumule, appels d'ecriture a executer par l'appelant, ex. add_homework).
    Si le modele ne gere pas les outils, on bascule sur un contexte complet sans outils.
    """
    history = messages[-MAX_HISTORY_MESSAGES:]
    contents: List[Dict[str, Any]] = [
        {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"][:MAX_MESSAGE_CHARS]}]}
        for m in history
    ]
    # Gemini exige que la conversation commence par un message utilisateur
    while contents and contents[0]["role"] != "user":
        contents.pop(0)

    total: Dict[str, int] = {}

    if model not in _NO_TOOLS_MODELS:
        tools = READ_TOOLS_DECL + ADD_HOMEWORK_TOOL
        try:
            for round_no in range(MAX_TOOL_ROUNDS + 1):
                last = round_no == MAX_TOOL_ROUNDS
                text, usage, calls, parts = _generate(api_key, model, SYSTEM_PROMPT + context, contents, MAX_OUTPUT_TOKENS, None if last else tools)
                _add_usage(total, usage)
                writes = [c for c in calls if c.get("name") not in READ_TOOL_NAMES_SET]
                reads = [c for c in calls if c.get("name") in READ_TOOL_NAMES_SET]
                if writes or not reads:
                    return text, total, writes
                # On renvoie au modele sa propre demande (parts d'origine) puis les resultats des outils
                contents.append({"role": "model", "parts": parts})
                contents.append({"role": "user", "parts": [
                    {"functionResponse": {"name": c["name"], "response": {"result": run_tool(c["name"], c.get("args") or {})}}}
                    for c in reads
                ]})
        except GeminiError as e:
            if not e.tools_unsupported:
                raise
            _NO_TOOLS_MODELS.add(model)
            contents = [c for c in contents if all("text" in p for p in c["parts"])]

    text, usage, _, _ = _generate(api_key, model, SYSTEM_PROMPT_NO_TOOLS + full_context(), contents, MAX_OUTPUT_TOKENS)
    _add_usage(total, usage)
    return text, total, []
