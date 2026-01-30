"""
Exécution AdHoc (commandes, scripts, URLs) pour un projet.
"""

from typing import Any

from rundeck.base import RundeckObjectManager
from rundeck.v1.objects.executions import Execution


class AdhocManager(RundeckObjectManager[Execution]):
    """Manager pour les exécutions AdHoc d'un projet."""

    _obj_cls = Execution

    def _project_name(self, project: str | None) -> str:
        project_name = project or (self.parent.id if self.parent else None)
        if not project_name:
            raise ValueError("Le nom du projet est requis pour les commandes AdHoc")
        return project_name

    def _wrap_execution(self, result: Any, refresh: bool = True) -> Execution:
        data = (
            result.get("execution")
            if isinstance(result, dict) and "execution" in result
            else result
        )
        if isinstance(data, dict):
            exec_id = data.get("id")
            # Les réponses AdHoc ne sont pas complètes,
            # Le rafraîchissement permet d'obtenir toutes les données
            if refresh and exec_id:
                try:
                    return self.rd.executions.get(exec_id)
                except Exception:
                    return Execution(self.rd.executions, data)
        return Execution(self.rd.executions, data)

    def run_command(
        self,
        exec: str,
        project: str | None = None,
        refresh: bool = True,
        **options: Any,
    ) -> Execution:
        """Exécute une commande shell AdHoc."""
        project_name = self._project_name(project)
        payload: dict[str, Any] = {"exec": exec, "project": project_name}
        payload.update(options)
        path = f"/project/{project_name}/run/command"
        result = self.rd.http_post(path, json=payload)
        return self._wrap_execution(result, refresh=refresh)

    def run_script(
        self,
        script: str | None = None,
        project: str | None = None,
        refresh: bool = True,
        script_file: tuple[str, Any, str | None] | None = None,
        **options: Any,
    ) -> Execution:
        """Exécute un script AdHoc (contenu inline ou multipart)."""
        project_name = self._project_name(project)
        path = f"/project/{project_name}/run/script"
        if script_file:
            filename, content, content_type = script_file
            payload: dict[str, Any] = {"project": project_name}
            payload.update(options)
            files = {"scriptFile": (filename, content, content_type or "text/plain")}
            result = self.rd.http_post(path, data=payload, files=files)
        else:
            payload: dict[str, Any] = {"script": script or "", "project": project_name}
            payload.update(options)
            result = self.rd.http_post(path, json=payload)
        return self._wrap_execution(result, refresh=refresh)

    def run_url(
        self,
        script_url: str,
        project: str | None = None,
        refresh: bool = True,
        **options: Any,
    ) -> Execution:
        """Exécute un script AdHoc depuis une URL."""
        project_name = self._project_name(project)
        payload: dict[str, Any] = {"scriptURL": script_url, "project": project_name}
        payload.update(options)
        path = f"/project/{project_name}/run/url"
        result = self.rd.http_post(path, json=payload)
        return self._wrap_execution(result, refresh=refresh)


__all__ = ["AdhocManager"]
