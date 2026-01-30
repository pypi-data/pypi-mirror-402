"""
Gestion des endpoints /scheduler
"""

from typing import Any

from rundeck.base import RundeckObjectManager


class SchedulerManager(RundeckObjectManager):
    """Manager pour les opérations du scheduler (/scheduler/*)."""

    _path = "/scheduler"

    def takeover(
        self,
        server_uuid: str | None = None,
        all_servers: bool = False,
        project: str | None = None,
        job_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Reprend le planning des jobs en mode cluster.

        Args:
            server_uuid: UUID du serveur cible.
            all_servers: True pour reprendre tous les serveurs.
            project: Projet concerné (optionnel).
            job_id: Job spécifique (optionnel).

        Returns:
            Résultat de la reprise.
        """
        path = self._build_path("takeover")

        data: dict[str, Any] = {}
        if all_servers:
            data["server"] = {"all": True}
        elif server_uuid:
            data["server"] = {"uuid": server_uuid}

        if project:
            data["project"] = project
        if job_id:
            data["job"] = {"id": job_id}

        return self.rd.http_put(path, json=data)


__all__ = ["SchedulerManager"]
