"""
Gestion des jobs Rundeck
"""

from typing import Any

from rundeck.base import RundeckObject, RundeckObjectManager
from rundeck.v1.objects.executions import Execution
from rundeck.v1.objects.scm import JobSCMManager


class Job(RundeckObject):
    """Représente un job Rundeck."""

    _id_attr = "id"
    _repr_attr = "name"

    def _job_path(self, suffix: str | None = None) -> str:
        """Construit le chemin de base /job/{id} avec suffixe optionnel."""
        base = f"/job/{self.id}"
        if suffix:
            return f"{base}/{suffix.lstrip('/')}"
        return base

    def run(
        self, as_execution: bool = False, **kwargs: Any
    ) -> Execution | dict[str, Any]:
        """
        Exécute le job et retourne la réponse brute par défaut.

        Args:
            as_execution: True pour envelopper la réponse en Execution.
        """
        path = self._job_path("run")
        result = self.rd.http_post(path, json=kwargs or None)
        if as_execution:
            # Wrap avec le manager d'exécutions existant.
            return Execution(self.manager.rd.executions, result)
        return result

    def retry(
        self,
        execution_id: str,
        as_execution: bool = False,
        **kwargs: Any,
    ) -> Execution | dict[str, Any]:
        """
        Relance une exécution (retry).

        Args:
            execution_id: ID de l'exécution à relancer.
            as_execution: True pour envelopper la réponse en Execution.
        """
        path = self._job_path(f"retry/{execution_id}")
        result = self.rd.http_post(path, json=kwargs or None)
        if as_execution:
            return Execution(self.manager.rd.executions, result)
        return result

    def delete(self) -> None:
        """Supprime le job courant."""
        self.manager.delete(self.id)

    def definition(self, format: str = "json") -> Any:
        """Récupère la définition du job dans le format demandé."""
        path = self._job_path()
        return self.rd.http_get(path, params={"format": format})

    def enable_execution(self) -> Any:
        """Active l'exécution pour ce job."""
        path = self._job_path("execution/enable")
        return self.rd.http_post(path)

    def disable_execution(self) -> Any:
        """Désactive l'exécution pour ce job."""
        path = self._job_path("execution/disable")
        return self.rd.http_post(path)

    def enable_schedule(self) -> Any:
        """Active la planification pour ce job."""
        path = self._job_path("schedule/enable")
        return self.rd.http_post(path)

    def disable_schedule(self) -> Any:
        """Désactive la planification pour ce job."""
        path = self._job_path("schedule/disable")
        return self.rd.http_post(path)

    def info(self) -> dict[str, Any]:
        """Récupère les métadonnées du job."""
        path = self._job_path("info")
        return self.rd.http_get(path)

    def workflow(self) -> dict[str, Any]:
        """Récupère le workflow du job."""
        path = self._job_path("workflow")
        return self.rd.http_get(path)

    def meta(self, meta: str | None = None) -> list[dict[str, Any]]:
        """
        Récupère les métadonnées UI du job (endpoint /job/{id}/meta).

        Args:
            meta: Liste de métadonnées à inclure (ex: "name,description")
                ou "*" pour tout.
        """
        params = {"meta": meta} if meta else None
        path = self._job_path("meta")
        return self.rd.http_get(path, params=params)

    def tags(self) -> list[str]:
        """Retourne les tags du job (commercial, endpoint /job/{id}/tags)."""
        path = self._job_path("tags")
        return self.rd.http_get(path)

    def upload_option_file(
        self,
        option_name: str,
        content: bytes | str,
        file_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Upload d'un fichier pour une option (single file).
        """
        path = self._job_path("input/file")
        params = {"optionName": option_name}
        if file_name:
            params["fileName"] = file_name
        response = self.rd.http_post(
            path,
            params=params,
            data=content,
            headers={
                "Content-Type": "application/octet-stream",
                "Accept": "application/json",
            },
            raw=True,
        )
        return response.json()

    def upload_option_files(
        self, files: dict[str, tuple[str, bytes | Any]]
    ) -> dict[str, Any]:
        """
        Upload multi-fichiers pour des options (multipart/form-data).

        Args:
            files: mapping option_name -> (file_name, content)
        """
        multipart: dict[str, tuple[str, bytes | Any]] = {
            f"option.{name}": (fname, data) for name, (fname, data) in files.items()
        }
        path = self._job_path("input/file")
        response = self.rd.http_post(
            path,
            files=multipart,
            headers={"Accept": "application/json"},
            raw=True,
        )
        return response.json()

    def list_uploaded_files(
        self,
        max: int | None = None,
        offset: int | None = None,
        file_state: str | None = None,
    ) -> dict[str, Any]:
        """
        Liste les fichiers uploadés pour ce job.
        """
        params: dict[str, Any] = {}
        if max is not None:
            params["max"] = max
        if offset is not None:
            params["offset"] = offset
        if file_state:
            params["fileState"] = file_state
        path = f"/job/{self.id}/input/files"
        return self.rd.http_get(path, params=params or None)

    def forecast(
        self, time: str | None = None, max: int | None = None
    ) -> dict[str, Any]:
        """Prévision du planning du job (scheduler/forecast)."""
        params: dict[str, Any] = {}
        if time:
            params["time"] = time
        if max:
            params["max"] = max
        path = f"/scheduler/{self._job_path('forecast').lstrip('/')}"
        return self.rd.http_get(path, params=params)

    @property
    def scm(self) -> JobSCMManager:
        """Accès aux opérations SCM pour ce job."""
        return JobSCMManager(self.rd, parent=self)


class JobBulkManager(RundeckObjectManager[Job]):
    """Opérations bulk sur les jobs (/jobs/*)."""

    _path = "/jobs"
    _obj_cls = Job

    def enable_execution(self, ids: "list[str]") -> Any:
        """Active l'exécution pour plusieurs jobs."""
        data = {"ids": ids}
        path = self._build_path("execution/enable")
        return self.rd.http_put(path, json=data)

    def disable_execution(self, ids: "list[str]") -> Any:
        """Désactive l'exécution pour plusieurs jobs."""
        data = {"ids": ids}
        path = self._build_path("execution/disable")
        return self.rd.http_put(path, json=data)

    def enable_schedule(self, ids: "list[str]") -> Any:
        """Active la planification pour plusieurs jobs."""
        data = {"ids": ids}
        path = self._build_path("schedule/enable")
        return self.rd.http_post(path, json=data)

    def disable_schedule(self, ids: "list[str]") -> Any:
        """Désactive la planification pour plusieurs jobs."""
        data = {"ids": ids}
        path = self._build_path("schedule/disable")
        return self.rd.http_post(path, json=data)

    def delete(self, ids: "list[str]") -> Any:
        """Supprime plusieurs jobs en une requête."""
        data = {"ids": ids}
        path = self._build_path("delete")
        return self.rd.http_delete(path, json=data)


class JobManager(RundeckObjectManager[Job]):
    """Manager pour les jobs."""

    _path = "/project/{parent}/jobs"
    _obj_cls = Job

    def __init__(self, rd: Any, parent: RundeckObject | None = None) -> None:
        super().__init__(rd, parent)
        self.bulk = JobBulkManager(rd)

    def __getattr__(self, name: str) -> Any:
        # Alias pour permettre rd.jobs.import(...) malgré le mot-clé Python.
        if name == "import":
            return self.import_jobs
        return super().__getattribute__(name)

    def list(
        self,
        project: str | None = None,
        **filters: Any,
    ) -> "list[Job]":
        """Liste les jobs d'un projet."""
        project_name = project or (self.parent.id if self.parent else None)
        # Avec un parent Project, on réutilise le manager parenté ; sinon on exige
        # le nom du projet.
        if not project_name:
            raise ValueError("Le paramètre project est requis")

        # Si le manager est parenté (project.jobs), _build_path() résout le
        # placeholder {parent}.
        # Sinon, on formate le chemin collection à partir du nom de projet fourni.
        path = (
            self._build_path()
            if self.parent and not project
            else self._path.format(parent=project_name)
        )
        return self._list(path=path, params=filters)

    def get(self, id: str) -> "Job":
        """Récupère un job par identifiant."""
        path = f"/job/{id}"
        return self._get(id, path=path)

    def export(
        self,
        project: str | None = None,
        format: str = "json",
        idlist: str | None = None,
        groupPath: str | None = None,
        jobFilter: str | None = None,
    ) -> Any:
        """Exporte les jobs d'un projet (json/xml/yaml)."""
        project_name = project or (self.parent.id if self.parent else None)
        if not project_name:
            raise ValueError("Le paramètre project est requis")

        params: dict[str, Any] = {"format": format} if format else {}
        if idlist:
            params["idlist"] = idlist
        if groupPath:
            params["groupPath"] = groupPath
        if jobFilter:
            params["jobFilter"] = jobFilter

        path = (
            self._build_path("export")
            if self.parent and not project
            else f"/project/{project_name}/jobs/export"
        )
        return self.rd.http_get(path, params=params or None)

    def import_jobs(
        self,
        project: str | None = None,
        content: Any = None,
        fileformat: str = "json",
        dupeOption: str | None = None,
        uuidOption: str | None = None,
        content_type: str = "application/octet-stream",
    ) -> Any:
        """Importe des jobs (json/xml/yaml) dans un projet."""
        project_name = project or (self.parent.id if self.parent else None)
        if not project_name:
            raise ValueError("Le paramètre project est requis")

        params: dict[str, Any] = {"fileformat": fileformat} if fileformat else {}
        if dupeOption:
            params["dupeOption"] = dupeOption
        if uuidOption:
            params["uuidOption"] = uuidOption

        path = (
            self._build_path("import")
            if self.parent and not project
            else f"/project/{project_name}/jobs/import"
        )
        return self.rd.http_post(
            path,
            params=params or None,
            data=content,
            headers={"Content-Type": content_type},
        )

    def delete(self, id: str) -> None:
        """Supprime un job par identifiant."""
        path = f"/job/{id}"
        self._delete(id, path=path)

    def get_uploaded_file_info(self, file_id: str) -> dict[str, Any]:
        """Récupère les métadonnées d'un fichier uploadé (par ID)."""
        path = f"/jobs/file/{file_id}"
        return self.rd.http_get(path)
