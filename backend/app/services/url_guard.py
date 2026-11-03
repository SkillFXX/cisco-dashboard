import ipaddress
import socket
import urllib.parse
from typing import Optional, Tuple

import requests

MAX_REDIRECTS = 3
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
BLOCKED_HOSTS = {"metadata.google.internal", "instance-data", "localhost"}


def _ip_is_forbidden(ip: ipaddress._BaseAddress) -> bool:
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def validate_service_url(url: str) -> Optional[str]:
    """Valide l'URL d'un service externe et bloque les cibles internes (SSRF).

    Le nom d'hote est resolu : toutes les adresses obtenues doivent etre publiques.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return "L'adresse doit commencer par http:// ou https://"
        host = parsed.hostname
        if not host:
            return "Nom d'hôte de l'URL invalide."
        if host.lower() in BLOCKED_HOSTS:
            return "Cette adresse n'est pas autorisée."

        try:
            addresses = [ipaddress.ip_address(host)]
        except ValueError:
            try:
                infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), proto=socket.IPPROTO_TCP)
            except socket.gaierror:
                return "Nom d'hôte introuvable."
            addresses = [ipaddress.ip_address(info[4][0]) for info in infos]

        if any(_ip_is_forbidden(ip) for ip in addresses):
            return "L'accès aux adresses IP privées ou locales est interdit."
        return None
    except Exception as e:
        return f"Format d'URL invalide : {e}"


def safe_get(url: str, timeout: int = 20, headers: Optional[dict] = None) -> Tuple[int, str]:
    """GET avec validation SSRF a chaque redirection et taille de reponse plafonnee."""
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        err = validate_service_url(current)
        if err:
            raise ValueError(err)
        with requests.get(current, timeout=timeout, headers=headers, allow_redirects=False, stream=True) as resp:
            if resp.is_redirect or resp.status_code in (301, 302, 303, 307, 308):
                location = resp.headers.get("Location")
                if not location:
                    raise ValueError("Redirection invalide.")
                current = urllib.parse.urljoin(current, location)
                continue
            body = b""
            for chunk in resp.iter_content(chunk_size=65536):
                body += chunk
                if len(body) > MAX_RESPONSE_BYTES:
                    raise ValueError("Réponse trop volumineuse.")
            resp.encoding = resp.encoding or "utf-8"
            return resp.status_code, body.decode(resp.encoding, errors="replace")
    raise ValueError("Trop de redirections.")
