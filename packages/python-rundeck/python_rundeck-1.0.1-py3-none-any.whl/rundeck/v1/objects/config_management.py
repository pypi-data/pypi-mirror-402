from __future__ import annotations

"""
Gestion de la configuration Rundeck (instance globale).
"""

from rundeck.base import RundeckObjectManager


class ConfigManagementManager(RundeckObjectManager):
    """
    Gestion des configurations globales (plugin/custom) via /config.
    """

    _path = "/config"

    def list(self) -> list[dict[str, str]]:
        """Liste toutes les configs et propriétés."""
        path = self._build_path("list")
        return self.rd.http_get(path)

    def save(self, entries: list[dict[str, str]]) -> dict[str, str | list[str]]:
        """
        Crée ou met à jour des configs (payload: liste de dicts {key, value, strata?}).
        """
        path = self._build_path("save")
        return self.rd.http_post(path, json=entries)

    def delete(self, key: str, strata: str | None = None) -> None:
        """
        Supprime une config via /config/delete avec payload JSON.
        """
        payload: dict[str, str] = {"key": key}
        if strata:
            payload["strata"] = strata
        path = self._build_path("delete")
        self.rd.http_delete(path, json=payload)

    def refresh(self) -> dict[str, str]:
        """
        Recharge les configurations depuis les fichiers de propriétés.
        """
        path = self._build_path("refresh")
        return self.rd.http_post(path)

    def restart(self) -> dict[str, str]:
        """
        Redémarre le serveur Rundeck.
        """
        path = self._build_path("restart")
        return self.rd.http_post(path)
