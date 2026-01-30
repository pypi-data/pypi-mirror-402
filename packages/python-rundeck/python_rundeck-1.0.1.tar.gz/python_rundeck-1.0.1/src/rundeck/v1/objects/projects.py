"""
Gestion des projets Rundeck
"""

from typing import Any

from rundeck.base import RundeckObject, RundeckObjectManager
from rundeck.v1.objects.adhoc import AdhocManager
from rundeck.v1.objects.executions import ExecutionManager
from rundeck.v1.objects.jobs import JobManager
from rundeck.v1.objects.scm import ProjectSCMManager
from rundeck.v1.objects.webhooks import ProjectWebhookManager


class Project(RundeckObject):
    """Représente un projet Rundeck."""

    _id_attr = "name"
    _repr_attr = "name"

    @property
    def jobs(self) -> JobManager:
        """Accès aux jobs du projet via un manager parenté."""
        return JobManager(self.rd, parent=self)

    @property
    def executions(self) -> ExecutionManager:
        """Accès aux exécutions du projet via un manager parenté."""
        return ExecutionManager(self.rd, parent=self)

    @property
    def config(self) -> "ProjectConfigManager":
        """Accès à la configuration du projet (clé/valeur)."""
        return ProjectConfigManager(self.rd, parent=self)

    @property
    def resources(self) -> "ProjectResourcesManager":
        """Accès aux ressources/nodes du projet."""
        return ProjectResourcesManager(self.rd, parent=self)

    @property
    def sources(self) -> "ProjectSourcesManager":
        """Accès aux sources de ressources du projet."""
        return ProjectSourcesManager(self.rd, parent=self)

    @property
    def acl(self) -> "ProjectACLManager":
        """Accès aux ACL du projet."""
        return ProjectACLManager(self.rd, parent=self)

    @property
    def archive(self) -> "ProjectArchiveManager":
        """Accès aux exports/imports d'archive projet."""
        return ProjectArchiveManager(self.rd, parent=self)

    @property
    def readme(self) -> "ProjectReadmeManager":
        """Accès aux fichiers readme/motd du projet."""
        return ProjectReadmeManager(self.rd, parent=self)

    @property
    def scm(self) -> ProjectSCMManager:
        """Accès aux opérations SCM du projet (import/export)."""
        return ProjectSCMManager(self.rd, parent=self)

    @property
    def webhooks(self) -> ProjectWebhookManager:
        """Accès aux webhooks du projet."""
        return ProjectWebhookManager(self.rd, parent=self)

    @property
    def adhoc(self) -> AdhocManager:
        """Accès aux commandes/scripts AdHoc du projet."""
        return AdhocManager(self.rd, parent=self)


class ProjectManager(RundeckObjectManager[Project]):
    """Manager pour les projets."""

    _path = "/projects"
    _obj_cls = Project

    def list(self) -> list[Project]:
        """Liste tous les projets."""
        return self._list()

    def get(self, name: str) -> Project:
        """Récupère un projet par son nom."""
        path = f"/project/{name}"
        return self._get(name, path=path)

    def create(self, name: str, config: dict[str, Any] | None = None) -> Project:
        """Crée un projet (optionnellement avec configuration)."""
        payload: dict[str, Any] = {"name": name}
        if config:
            payload["config"] = config
        path = self._build_path()
        return self._create(json=payload, path=path)

    def delete(self, name: str) -> None:
        """Supprime un projet par son nom."""
        path = f"/project/{name}"
        self._delete(name, path=path)


class ProjectConfig(RundeckObject):
    """Placeholder, non utilisé pour wrapping (retours dict)."""


class ProjectConfigManager(RundeckObjectManager[ProjectConfig]):
    """Manager pour la configuration d'un projet (clé/valeur)."""

    _path = "/project/{parent}/config"
    _obj_cls = ProjectConfig

    @property
    def keys(self) -> "ProjectConfigKeysManager":
        """Opérations clé/valeur (GET/PUT/POST/DELETE)."""
        return ProjectConfigKeysManager(self.rd, parent=self.parent)

    def get(self) -> dict[str, str]:
        """Récupère toute la configuration du projet parent."""
        path = self._build_path()
        return self.rd.http_get(path)

    def replace(self, config: dict[str, str]) -> dict[str, str]:
        """Remplace toute la configuration du projet."""
        path = self._build_path()
        return self.rd.http_put(path, json=config)


class ProjectConfigKeysManager(RundeckObjectManager[ProjectConfig]):
    """Opérations par clé sur la configuration."""

    _path = "/project/{parent}/config"
    _obj_cls = ProjectConfig

    def get(self, key: str) -> dict[str, str]:
        """Récupère une propriété de configuration."""
        path = self._build_path(key)
        return self.rd.http_get(path)

    def set(self, key: str, value: str) -> dict[str, str]:
        """Définit une propriété de configuration."""
        path = self._build_path(key)
        return self.rd.http_put(path, json={"value": value})

    def update(self, config: dict[str, str]) -> dict[str, str]:
        """Met à jour plusieurs propriétés en une fois."""
        path = self._build_path()
        return self.rd.http_post(path, json=config)

    def delete(self, key: str) -> None:
        """Supprime une propriété de configuration."""
        path = self._build_path(key)
        self.rd.http_delete(path)


class ProjectACLManager(RundeckObjectManager):
    """Manager pour les ACL d'un projet (/project/{parent}/acl)."""

    _path = "/project/{parent}/acl"

    def list(self) -> dict[str, Any]:
        """Liste les politiques ACL du projet."""
        path = self._build_path("")
        return self.rd.http_get(path)

    def get(self, policy_name: str) -> str:
        """Récupère une politique ACL projet (contenu texte)."""
        path = self._build_path(policy_name)
        response = self.rd.http_get(path, raw=True)
        return response.text

    def create(self, policy_name: str, content: str) -> dict[str, Any]:
        """Crée une politique ACL projet."""
        path = self._build_path(policy_name)
        headers = {"Content-Type": "application/yaml"}
        return self.rd.http_post(path, data=content, headers=headers)

    def update(self, policy_name: str, content: str) -> dict[str, Any]:
        """Met à jour une politique ACL projet."""
        path = self._build_path(policy_name)
        headers = {"Content-Type": "application/yaml"}
        return self.rd.http_put(path, data=content, headers=headers)

    def delete(self, policy_name: str) -> None:
        """Supprime une politique ACL projet."""
        path = self._build_path(policy_name)
        self.rd.http_delete(path)


class ProjectResourcesManager(RundeckObjectManager):
    """Manager pour les ressources (nodes) d'un projet."""

    _path = "/project/{parent}/resources"
    _obj_cls = RundeckObject  # non utilisé, on retourne les données brutes

    def list(self, format: str | None = "json", **filters: Any) -> Any:
        """Liste les ressources du projet (avec filtres de nodes éventuels)."""
        params: dict[str, Any] = {}
        if format:
            params["format"] = format
        params.update(filters)
        path = self._build_path()
        return self.rd.http_get(path, params=params or None)

    def get(self, name: str, format: str | None = "json") -> Any:
        """Récupère une ressource spécifique par son nom."""
        params: dict[str, Any] = {"format": format} if format else None
        path = (
            f"/project/{self.parent.id}/resource/{name}"
            if self.parent
            else f"/resource/{name}"
        )
        return self.rd.http_get(path, params=params)


class ProjectSourcesManager(RundeckObjectManager):
    """Manager pour les sources de ressources d'un projet."""

    _path = "/project/{parent}/sources"
    _obj_cls = RundeckObject  # on retourne les dicts tels quels

    def list(self) -> Any:
        """Liste les sources de ressources du projet."""
        path = self._build_path()
        return self.rd.http_get(path)

    def get(self, index: int) -> Any:
        """Récupère une source spécifique par son index."""
        path = self._build_path(f"{index}")
        return self.rd.http_get(path)

    def list_resources(self, index: int, accept: str | None = None) -> Any:
        """Liste les ressources d'une source donnée."""
        path = self._build_path(f"{index}/resources")
        headers = {"Accept": accept} if accept else None
        return self.rd.http_get(path, headers=headers)

    def update_resources(
        self,
        index: int,
        content: Any,
        content_type: str = "application/json",
        accept: str | None = None,
    ) -> Any:
        """Met à jour les ressources d'une source via POST."""
        path = self._build_path(f"{index}/resources")
        headers: dict[str, str] = {"Content-Type": content_type}
        if accept:
            headers["Accept"] = accept
        return self.rd.http_post(path, data=content, headers=headers)


class ProjectReadmeManager(RundeckObjectManager):
    """Gestion des fichiers readme.md / motd.md d'un projet."""

    _path = "/project/{parent}"

    def _get_file(self, filename: str, accept: str | None = "text/plain") -> Any:
        headers = {"Accept": accept} if accept else None
        path = self._build_path(filename)
        return self.rd.http_get(path, headers=headers)

    def _put_file(
        self, filename: str, content: Any, content_type: str = "text/plain"
    ) -> Any:
        path = self._build_path(filename)
        headers = {"Content-Type": content_type}
        if content_type == "application/json" and isinstance(content, str):
            payload = {"contents": content}
            return self.rd.http_put(path, json=payload, headers=headers)
        return self.rd.http_put(path, data=content, headers=headers)

    def _delete_file(self, filename: str) -> None:
        path = self._build_path(filename)
        self.rd.http_delete(path)

    def get_readme(self, accept: str | None = "text/plain") -> Any:
        """Récupère le readme du projet (texte ou JSON selon l'Accept)."""
        return self._get_file("readme.md", accept=accept)

    def update_readme(self, content: Any, content_type: str = "text/plain") -> Any:
        """Crée ou met à jour le readme du projet."""
        return self._put_file("readme.md", content=content, content_type=content_type)

    def delete_readme(self) -> None:
        """Supprime le readme du projet."""
        self._delete_file("readme.md")

    def get_motd(self, accept: str | None = "text/plain") -> Any:
        """Récupère le motd (Message of the Day) du projet."""
        return self._get_file("motd.md", accept=accept)

    def update_motd(self, content: Any, content_type: str = "text/plain") -> Any:
        """Crée ou met à jour le motd du projet."""
        return self._put_file("motd.md", content=content, content_type=content_type)

    def delete_motd(self) -> None:
        """Supprime le motd du projet."""
        self._delete_file("motd.md")


class ProjectArchiveManager(RundeckObjectManager):
    """Manager pour l'export/import d'un projet complet."""

    _path = "/project/{parent}"

    def export(
        self,
        execution_ids: list[str] | str | None = None,
        export_all: bool | None = None,
        export_jobs: bool | None = None,
        export_executions: bool | None = None,
        export_configs: bool | None = None,
        export_readmes: bool | None = None,
        export_acls: bool | None = None,
        export_scm: bool | None = None,
        export_webhooks: bool | None = None,
        whkIncludeAuthTokens: bool | None = None,
        **components: Any,
    ) -> Any:
        """
        Exporte une archive ZIP du projet (synchrone).

        Retourne la réponse brute (zip) pour laisser l'appelant gérer le flux.
        """
        params: dict[str, Any] = {}
        if execution_ids:
            if isinstance(execution_ids, list):
                params["executionIds"] = ",".join(execution_ids)
            else:
                params["executionIds"] = execution_ids
        if export_all is not None:
            params["exportAll"] = export_all
        if export_jobs is not None:
            params["exportJobs"] = export_jobs
        if export_executions is not None:
            params["exportExecutions"] = export_executions
        if export_configs is not None:
            params["exportConfigs"] = export_configs
        if export_readmes is not None:
            params["exportReadmes"] = export_readmes
        if export_acls is not None:
            params["exportAcls"] = export_acls
        if export_scm is not None:
            params["exportScm"] = export_scm
        if export_webhooks is not None:
            params["exportWebhooks"] = export_webhooks
        if whkIncludeAuthTokens is not None:
            params["whkIncludeAuthTokens"] = whkIncludeAuthTokens
        if components:
            params.update(components)
        path = self._build_path("export")
        return self.rd.http_get(path, params=params or None, raw=True)

    def export_async(self, **params: Any) -> Any:
        """Lance une export async, retourne le token."""
        path = self._build_path("export/async")
        return self.rd.http_get(path, params=params or None)

    def export_status(self, token: str) -> Any:
        """Vérifie le statut d'un export async."""
        path = self._build_path(f"export/status/{token}")
        return self.rd.http_get(path)

    def export_download(self, token: str) -> Any:
        """Télécharge l'archive d'un export async prêt."""
        path = self._build_path(f"export/download/{token}")
        return self.rd.http_get(path, raw=True)

    def import_archive(
        self,
        content: Any,
        async_import: bool | None = None,
        jobUuidOption: str | None = None,
        importExecutions: bool | None = None,
        importConfig: bool | None = None,
        importACL: bool | None = None,
        importScm: bool | None = None,
        importWebhooks: bool | None = None,
        whkRegenAuthTokens: bool | None = None,
        importNodesSources: bool | None = None,
        **component_options: Any,
    ) -> Any:
        """
        Importe une archive ZIP dans le projet.
        """
        params: dict[str, Any] = {}
        if async_import is not None:
            params["asyncImport"] = async_import
        if jobUuidOption:
            params["jobUuidOption"] = jobUuidOption
        if importExecutions is not None:
            params["importExecutions"] = importExecutions
        if importConfig is not None:
            params["importConfig"] = importConfig
        if importACL is not None:
            params["importACL"] = importACL
        if importScm is not None:
            params["importScm"] = importScm
        if importWebhooks is not None:
            params["importWebhooks"] = importWebhooks
        if whkRegenAuthTokens is not None:
            params["whkRegenAuthTokens"] = whkRegenAuthTokens
        if importNodesSources is not None:
            params["importNodesSources"] = importNodesSources
        if component_options:
            params.update(component_options)

        path = self._build_path("import")
        headers = {"Content-Type": "application/zip"}
        return self.rd.http_put(
            path, params=params or None, data=content, headers=headers
        )

    def import_status(self) -> Any:
        """Statut d'un import asynchrone."""
        path = self._build_path("import/status")
        return self.rd.http_get(path)
