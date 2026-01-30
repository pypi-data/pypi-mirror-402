from __future__ import annotations

"""
Gestion de la configuration Rundeck (arguments, variables d'env, fichiers).
"""

import configparser
import os
from pathlib import Path
from typing import Any

from rundeck.const import DEFAULT_API_VERSION, DEFAULT_TIMEOUT, USER_AGENT

DEFAULT_CONFIG_FILES: list[str] = [
    "/etc/rundeck.cfg",
    str(Path.home() / ".rundeck.cfg"),
]


class RundeckConfigError(Exception):
    """Erreur de configuration Rundeck."""


def _resolve_existing_files(config_files: list[str]) -> list[str]:
    existing: list[str] = []
    for file in config_files:
        path = Path(file).expanduser()
        if path.exists():
            existing.append(str(path.resolve()))
    return existing


def _coerce_timeout(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT


def _coerce_ssl_verify(value: Any) -> bool | str:
    if isinstance(value, bool):
        return value
    if value is None:
        return True
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    # Assume path to CA bundle
    return value


class RundeckConfig:
    """Charge la configuration depuis args/env/fichiers avec priorité décroissante."""

    def __init__(
        self,
        url: str | None = None,
        token: str | None = None,
        username: str | None = None,
        password: str | None = None,
        api_version: int | str | None = None,
        timeout: float | None = None,
        ssl_verify: bool | str | None = None,
        config_files: list[str] | None = None,
        config_section: str = "rundeck",
    ) -> None:
        env_url = os.getenv("RUNDECK_URL")
        env_token = os.getenv("RUNDECK_TOKEN")
        env_username = os.getenv("RUNDECK_USERNAME")
        env_password = os.getenv("RUNDECK_PASSWORD")
        env_api_version = os.getenv("RUNDECK_API_VERSION")
        env_timeout = os.getenv("RUNDECK_TIMEOUT")
        env_ssl_verify = os.getenv("RUNDECK_SSL_VERIFY")
        env_user_agent = os.getenv("RUNDECK_USER_AGENT")

        files = self._resolve_files(config_files)
        file_conf = self._parse_files(files, config_section) if files else {}

        self.url: str | None = url or env_url or file_conf.get("url")
        self.token: str | None = token or env_token or file_conf.get("token")
        self.username: str | None = (
            username or env_username or file_conf.get("username")
        )
        self.password: str | None = (
            password or env_password or file_conf.get("password")
        )
        self.api_version: str = str(
            api_version
            or env_api_version
            or file_conf.get("api_version")
            or DEFAULT_API_VERSION
        )
        self.timeout: float = (
            float(timeout)
            if timeout is not None
            else _coerce_timeout(env_timeout or file_conf.get("timeout"))
        )
        self.ssl_verify: bool | str = (
            ssl_verify
            if ssl_verify is not None
            else _coerce_ssl_verify(env_ssl_verify or file_conf.get("ssl_verify"))
        )
        self.user_agent: str = (
            env_user_agent or file_conf.get("user_agent") or USER_AGENT
        )
        self.config_files = files

    @staticmethod
    def _resolve_files(config_files: list[str] | None) -> list[str]:
        if config_files:
            resolved = _resolve_existing_files(config_files)
            if not resolved:
                raise RundeckConfigError("Aucun fichier de configuration trouvé.")
            return resolved

        env_cfg = os.getenv("RUNDECK_CFG")
        if env_cfg:
            resolved = _resolve_existing_files([env_cfg])
            if not resolved:
                raise RundeckConfigError(
                    f"Fichier de configuration introuvable: {env_cfg}"
                )
            return resolved

        return _resolve_existing_files(DEFAULT_CONFIG_FILES)

    @staticmethod
    def _parse_files(
        files: list[str],
        section: str,
    ) -> dict[str, Any]:
        parser = configparser.ConfigParser()
        parser.read(files, encoding="utf-8")
        if not parser.has_section(section):
            return {}

        def _get(option: str) -> Any:
            try:
                return parser.get(section, option)
            except (configparser.NoSectionError, configparser.NoOptionError):
                return None

        return {
            "url": _get("url"),
            "token": _get("token"),
            "username": _get("username"),
            "password": _get("password"),
            "api_version": _get("api_version"),
            "timeout": _get("timeout"),
            "ssl_verify": _get("ssl_verify"),
            "user_agent": _get("user_agent"),
        }

    @classmethod
    def from_config(
        cls, config_section: str | None = None, config_files: list[str] | None = None
    ) -> "RundeckConfig":
        """
        Charge uniquement depuis fichiers/env (sans arguments explicites).
        """
        return cls(
            config_files=config_files,
            config_section=config_section or "rundeck",
        )
