"""
Gestion des endpoints SCM (import/export) pour les projets et jobs.
"""

from typing import Any

from rundeck.base import RundeckObjectManager


class _ProjectSCMBaseManager(RundeckObjectManager):
    """Base pour les sous-managers SCM projet (intègre l'intégration import/export)."""

    def __init__(self, rd: Any, parent: Any, integration: str) -> None:
        super().__init__(rd, parent)
        self.integration = integration

    def _base_path(self) -> str:
        if not self.parent:
            raise ValueError("Parent projet requis pour SCM")
        return f"/project/{self.parent.id}/scm/{self.integration}"


class ProjectSCMPluginsManager(_ProjectSCMBaseManager):
    """Découverte des plugins SCM pour un projet."""

    def list(self) -> Any:
        """Liste les plugins SCM disponibles pour l'intégration."""
        path = self._build_path("plugins")
        return self.rd.http_get(path)

    def input_fields(self, plugin_type: str) -> Any:
        """Champs de saisie pour un plugin donné."""
        path = self._build_path(f"plugin/{plugin_type}/input")
        return self.rd.http_get(path)


class ProjectSCMConfigManager(_ProjectSCMBaseManager):
    """Configuration et cycle de vie d'un plugin SCM pour un projet."""

    def setup(self, plugin_type: str, config: dict[str, Any]) -> Any:
        """Configure un plugin SCM pour le projet."""
        path = self._build_path(f"plugin/{plugin_type}/setup")
        payload = {"config": config}
        return self.rd.http_post(path, json=payload)

    def enable(self, plugin_type: str) -> Any:
        """Active le plugin SCM (idempotent)."""
        path = self._build_path(f"plugin/{plugin_type}/enable")
        return self.rd.http_post(path)

    def disable(self, plugin_type: str) -> Any:
        """Désactive le plugin SCM (idempotent)."""
        path = self._build_path(f"plugin/{plugin_type}/disable")
        return self.rd.http_post(path)

    def get(self) -> Any:
        """Récupère la configuration SCM du projet pour l'intégration."""
        path = self._build_path("config")
        return self.rd.http_get(path)


class ProjectSCMActionsManager(_ProjectSCMBaseManager):
    """Statut et actions SCM pour un projet."""

    def status(self) -> Any:
        """Statut SCM du projet pour l'intégration."""
        path = self._build_path("status")
        return self.rd.http_get(path)

    def input_fields(self, action_id: str) -> Any:
        """Champs attendus pour une action SCM projet."""
        path = self._build_path(f"action/{action_id}/input")
        return self.rd.http_get(path)

    def perform(
        self,
        action_id: str,
        input_values: dict[str, Any] | None = None,
        jobs: list[str] | None = None,
        items: list[str] | None = None,
        deleted: list[str] | None = None,
        deleted_jobs: list[str] | None = None,
    ) -> Any:
        """Exécute une action SCM projet (ex: commit/import/sync)."""
        payload: dict[str, Any] = {}
        if input_values is not None:
            payload["input"] = input_values
        if jobs:
            payload["jobs"] = jobs
        if items:
            payload["items"] = items
        if deleted:
            payload["deleted"] = deleted
        if deleted_jobs:
            payload["deletedJobs"] = deleted_jobs

        path = self._build_path(f"action/{action_id}")
        return self.rd.http_post(path, json=payload or None)


class ProjectSCMIntegrationManager(RundeckObjectManager):
    """Regroupe les sous-managers SCM projet pour une intégration (import/export)."""

    def __init__(self, rd: Any, parent: Any, integration: str) -> None:
        super().__init__(rd, parent)
        self.integration = integration

    @property
    def plugins(self) -> ProjectSCMPluginsManager:
        return ProjectSCMPluginsManager(
            self.rd, parent=self.parent, integration=self.integration
        )

    @property
    def config(self) -> ProjectSCMConfigManager:
        return ProjectSCMConfigManager(
            self.rd, parent=self.parent, integration=self.integration
        )

    @property
    def actions(self) -> ProjectSCMActionsManager:
        return ProjectSCMActionsManager(
            self.rd, parent=self.parent, integration=self.integration
        )


class ProjectSCMManager(RundeckObjectManager):
    """Manager racine SCM pour un projet, expose import/export."""

    def __init__(self, rd: Any, parent: Any) -> None:
        if parent is None:
            raise ValueError("Parent projet requis pour SCM")
        super().__init__(rd, parent)

    @property
    def import_(self) -> ProjectSCMIntegrationManager:
        """SCM import pour le projet."""
        return ProjectSCMIntegrationManager(
            self.rd, parent=self.parent, integration="import"
        )

    @property
    def export(self) -> ProjectSCMIntegrationManager:
        """SCM export pour le projet."""
        return ProjectSCMIntegrationManager(
            self.rd, parent=self.parent, integration="export"
        )

    def __getattr__(self, name: str) -> Any:
        if name == "import":
            return self.import_
        return super().__getattribute__(name)


class JobSCMManager(RundeckObjectManager):
    """Manager racine SCM pour un job, expose import/export."""

    def __init__(self, rd: Any, parent: Any) -> None:
        if parent is None:
            raise ValueError("Parent job requis pour SCM")
        super().__init__(rd, parent)

    @property
    def import_(self) -> "JobSCMIntegrationManager":
        """SCM import pour le job."""
        return JobSCMIntegrationManager(
            self.rd, parent=self.parent, integration="import"
        )

    @property
    def export(self) -> "JobSCMIntegrationManager":
        """SCM export pour le job."""
        return JobSCMIntegrationManager(
            self.rd, parent=self.parent, integration="export"
        )

    def __getattr__(self, name: str) -> Any:
        if name == "import":
            return self.import_
        return super().__getattribute__(name)


class JobSCMIntegrationManager(RundeckObjectManager):
    """Opérations SCM pour un job donné et une intégration (import/export)."""

    def __init__(self, rd: Any, parent: Any, integration: str) -> None:
        super().__init__(rd, parent)
        self.integration = integration

    def _base_path(self) -> str:
        if not self.parent:
            raise ValueError("Parent job requis pour SCM")
        return f"/job/{self.parent.id}/scm/{self.integration}"

    def status(self) -> Any:
        """Statut SCM du job pour l'intégration."""
        path = self._build_path("status")
        return self.rd.http_get(path)

    def diff(self) -> Any:
        """Diff SCM pour le job (si applicable)."""
        path = self._build_path("diff")
        return self.rd.http_get(path)

    def input_fields(self, action_id: str) -> Any:
        """Champs attendus pour une action SCM job."""
        path = self._build_path(f"action/{action_id}/input")
        return self.rd.http_get(path)

    def perform(
        self, action_id: str, input_values: dict[str, Any] | None = None
    ) -> Any:
        """Exécute une action SCM job."""
        payload: dict[str, Any] = {}
        if input_values is not None:
            payload["input"] = input_values
        path = self._build_path(f"action/{action_id}")
        return self.rd.http_post(path, json=payload or None)


__all__ = [
    "ProjectSCMManager",
    "ProjectSCMIntegrationManager",
    "ProjectSCMPluginsManager",
    "ProjectSCMConfigManager",
    "ProjectSCMActionsManager",
    "JobSCMManager",
    "JobSCMIntegrationManager",
]
