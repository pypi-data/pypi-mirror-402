from __future__ import annotations

"""
Exceptions et helpers pour l'API Rundeck.
"""

from typing import Any

import requests


class RundeckError(Exception):
    """Exception de base pour toutes les erreurs Rundeck."""

    def __init__(
        self,
        message: str = "",
        error_code: str | None = None,
        response: requests.Response | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.response = response
        self.response_code = response.status_code if response is not None else None

        # Stocke le corps de la réponse (JSON ou texte brut)
        if response is None or not response.text:
            self.response_body: Any | None = None
        else:
            try:
                self.response_body = response.json()
            except ValueError:
                self.response_body = response.text

    def __str__(self) -> str:
        code = f"{self.response_code}: " if self.response_code is not None else ""
        error = f" ({self.error_code})" if self.error_code else ""
        return f"{code}{self.message}{error}"


class RundeckHTTPError(RundeckError):
    """Erreur HTTP générique renvoyée par Rundeck."""


class RundeckOperationError(RundeckHTTPError):
    """Erreur lors d'une opération métier."""


class RundeckAuthenticationError(RundeckOperationError):
    """Authentification ou autorisation refusée."""


class RundeckNotFoundError(RundeckOperationError):
    """Ressource introuvable."""


class RundeckValidationError(RundeckOperationError):
    """Entrée invalide (erreur 400)."""


class RundeckApiVersionUnsupportedError(RundeckValidationError):
    """Version d'API non supportée pour la ressource demandée."""


class RundeckConflictError(RundeckOperationError):
    """Conflit (erreur 409)."""


class RundeckQuotaExceededError(RundeckOperationError):
    """Quota dépassé (erreur 429)."""


class RundeckServerError(RundeckHTTPError):
    """Erreur serveur (5xx)."""


class RundeckConnectionError(RundeckError):
    """Erreur réseau ou connexion refusée."""


class RundeckTimeoutError(RundeckError):
    """Timeout réseau."""


def _extract_error(response: requests.Response) -> tuple[str, str | None, Any | None]:
    """
    Extrait le message et le code d'erreur depuis la réponse HTTP.
    """
    message = f"HTTP {response.status_code}"
    error_code: str | None = None
    body: Any | None = None

    if response.text:
        try:
            body = response.json()
        except ValueError:
            body = response.text

    if isinstance(body, dict):
        message = (
            body.get("message")
            or body.get("error")
            or body.get("errorMessage")
            or message
        )
        error_code = body.get("errorCode") or body.get("error_code")
    elif isinstance(body, str) and body.strip():
        message = body.strip()

    return message, error_code, body


def raise_for_status(response: requests.Response) -> None:
    """
    Lève une exception spécialisée en fonction du code HTTP.
    """
    message, error_code, body = _extract_error(response)
    status = response.status_code
    code_lower = error_code.lower() if isinstance(error_code, str) else None

    # Certains retours peuvent être HTTP 200 mais contenir un errorCode explicite
    if (
        response.ok
        and not code_lower
        and not (isinstance(body, dict) and body.get("error") is True)
    ):
        return

    if code_lower == "unauthorized":
        raise RundeckAuthenticationError(message, error_code, response)
    if code_lower == "api-version-unsupported":
        raise RundeckApiVersionUnsupportedError(message, error_code, response)
    if status == 400:
        raise RundeckValidationError(message, error_code, response)
    if status in (401, 403):
        raise RundeckAuthenticationError(message, error_code, response)
    if status == 404:
        raise RundeckNotFoundError(message, error_code, response)
    if status == 409:
        raise RundeckConflictError(message, error_code, response)
    if status == 429:
        raise RundeckQuotaExceededError(message, error_code, response)
    if status >= 500:
        raise RundeckServerError(message, error_code, response)

    raise RundeckHTTPError(message, error_code, response)


__all__ = [
    "RundeckApiVersionUnsupportedError",
    "RundeckAuthenticationError",
    "RundeckConflictError",
    "RundeckConnectionError",
    "RundeckError",
    "RundeckHTTPError",
    "RundeckNotFoundError",
    "RundeckOperationError",
    "RundeckQuotaExceededError",
    "RundeckServerError",
    "RundeckTimeoutError",
    "RundeckValidationError",
    "raise_for_status",
]
