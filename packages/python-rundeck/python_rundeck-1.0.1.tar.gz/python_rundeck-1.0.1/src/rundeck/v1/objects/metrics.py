"""
Gestion des métriques Rundeck
"""

from typing import Any

from rundeck.base import RundeckObjectManager


class MetricsManager(RundeckObjectManager):
    """Manager pour les endpoints de métriques."""

    _path = "/metrics"

    def list(self) -> dict[str, Any]:
        """Liste les endpoints de métriques disponibles."""
        path = self._build_path()
        return self.rd.http_get(path)

    def data(self) -> dict[str, Any]:
        """Récupère les données de métriques."""
        path = self._build_path("metrics")
        return self.rd.http_get(path)

    def healthcheck(self) -> dict[str, Any]:
        """Récupère les résultats des health checks."""
        path = self._build_path("healthcheck")
        return self.rd.http_get(path)

    def ping(self) -> str:
        """Ping du serveur via l'endpoint métriques."""
        path = self._build_path("ping")
        response = self.rd.http_get(path, raw=True)
        return response.text


__all__ = ["MetricsManager"]
