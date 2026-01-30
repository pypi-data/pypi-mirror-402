"""
Gestion des exécutions Rundeck
"""

from typing import Any

from rundeck.base import RundeckObject, RundeckObjectManager


class Execution(RundeckObject):
    """Représente une exécution Rundeck"""

    _id_attr = "id"

    def abort(self, asUser: str | None = None) -> dict[str, Any]:
        """
        Annule l'exécution

        Args:
            asUser: Annuler en tant qu'utilisateur

        Returns:
            Statut de l'annulation
        """
        path = f"/execution/{self.id}/abort"

        data = {}
        if asUser:
            data["asUser"] = asUser

        return self.manager.rd.http_get(path, params=data)

    def get_output(
        self,
        offset: int = 0,
        lastlines: int | None = None,
        lastmod: int | None = None,
        maxlines: int | None = None,
    ) -> dict[str, Any]:
        """
        Récupère la sortie de l'exécution

        Args:
            offset: Offset dans la sortie
            lastlines: Nombre de dernières lignes
            lastmod: Timestamp de dernière modification
            maxlines: Nombre maximum de lignes

        Returns:
            Sortie de l'exécution
        """
        path = f"/execution/{self.id}/output"

        params: dict[str, Any] = {"offset": offset}
        if lastlines:
            params["lastlines"] = lastlines
        if lastmod:
            params["lastmod"] = lastmod
        if maxlines:
            params["maxlines"] = maxlines

        return self.manager.rd.http_get(path, params=params)

    def get_state(self) -> dict[str, Any]:
        """
        Récupère l'état de l'exécution

        Returns:
            État de l'exécution
        """
        path = f"/execution/{self.id}/state"
        return self.manager.rd.http_get(path)

    def delete(self) -> None:
        """Supprime l'exécution"""
        self.manager.delete(self.id)

    def is_running(self) -> bool:
        """
        Vérifie si l'exécution est en cours

        Returns:
            True si en cours, False sinon
        """
        return self._attrs.get("status") == "running"

    def is_succeeded(self) -> bool:
        """
        Vérifie si l'exécution a réussi

        Returns:
            True si réussie, False sinon
        """
        return self._attrs.get("status") == "succeeded"

    def is_failed(self) -> bool:
        """
        Vérifie si l'exécution a échoué

        Returns:
            True si échouée, False sinon
        """
        return self._attrs.get("status") in ("failed", "failed-with-retry")

    def is_aborted(self) -> bool:
        """
        Vérifie si l'exécution a été annulée

        Returns:
            True si annulée, False sinon
        """
        return self._attrs.get("status") == "aborted"

    def refresh(self) -> None:
        """
        Actualise les données de l'exécution

        Returns:
            None.
        """
        updated = self.manager.get(self.id)
        self._attrs = updated._attrs


class ExecutionManager(RundeckObjectManager):
    """Manager pour les exécutions"""

    _path = "/executions"
    _obj_cls = Execution

    def list(
        self,
        project: str | None = None,
        status: str | None = None,
        max: int | None = None,
        offset: int | None = None,
        **kwargs: Any,
    ) -> "list[Execution]":
        """
        Liste les exécutions

        Args:
            project: Filtre par projet
            status: Filtre par statut
            max: Nombre maximum de résultats
            offset: Offset de pagination
            **kwargs: Autres paramètres de filtrage

        Returns:
            Liste d'exécutions
        """
        project_name = project or (
            self.parent.id if getattr(self, "parent", None) else None
        )
        if project_name:
            path = f"/project/{project_name}/executions"
        else:
            path = self._build_path()

        params: dict[str, Any] = {}
        if status:
            params["status"] = status
        if max:
            params["max"] = max
        if offset:
            params["offset"] = offset
        params.update(kwargs)

        return self._list(path=path, params=params or None)

    def running(self, project: str | None = None) -> "list[Execution]":
        """
        Liste les exécutions en cours

        Args:
            project: Filtre par projet (ou '*' pour tous)

        Returns:
            Liste d'exécutions en cours
        """
        project_name = project or (
            self.parent.id if getattr(self, "parent", None) else None
        )
        if project_name:
            path = f"/project/{project_name}/executions/running"
        else:
            path = "/project/*/executions/running"

        return self._list(path=path)

    def get(self, id: str) -> Execution:
        """
        Récupère une exécution par son ID

        Args:
            id: ID de l'exécution

        Returns:
            Exécution
        """
        path = f"/execution/{id}"
        return self._get(id, path=path)

    def delete(self, id: str) -> None:
        """
        Supprime une exécution

        Args:
            id: ID de l'exécution
        """
        path = f"/execution/{id}"
        self._delete(id, path=path)

    def bulk_delete(self, ids: "list[str]") -> dict[str, Any]:
        """
        Supprime plusieurs exécutions

        Args:
            ids: Liste d'IDs d'exécutions

        Returns:
            Résultat de la suppression
        """
        path = self._build_path("delete")
        data = {"ids": ids}
        return self.rd.http_post(path, json=data)

    def query(
        self,
        project: str,
        statusFilter: str | None = None,
        abortedbyFilter: str | None = None,
        userFilter: str | None = None,
        recentFilter: str | None = None,
        olderFilter: str | None = None,
        begin: str | None = None,
        end: str | None = None,
        adhoc: bool | None = None,
        jobIdListFilter: "list[str] | None" = None,
        excludeJobIdListFilter: "list[str] | None" = None,
        jobListFilter: "list[str] | None" = None,
        excludeJobListFilter: "list[str] | None" = None,
        groupPath: str | None = None,
        groupPathExact: str | None = None,
        excludeGroupPath: str | None = None,
        excludeGroupPathExact: str | None = None,
        jobExactFilter: str | None = None,
        excludeJobExactFilter: str | None = None,
        max: int | None = None,
        offset: int | None = None,
    ) -> "list[Execution]":
        """
        Requête avancée sur les exécutions

        Args:
            project: Nom du projet
            statusFilter: Filtre par statut
            abortedbyFilter: Filtre par utilisateur ayant annulé
            userFilter: Filtre par utilisateur
            recentFilter: Filtre par période récente
            olderFilter: Filtre par période ancienne
            begin: Date de début
            end: Date de fin
            adhoc: Exécutions adhoc uniquement
            jobIdListFilter: Liste d'IDs de jobs
            excludeJobIdListFilter: Exclure les IDs de jobs
            jobListFilter: Liste de noms de jobs
            excludeJobListFilter: Exclure les noms de jobs
            groupPath: Chemin de groupe
            groupPathExact: Chemin de groupe exact
            excludeGroupPath: Exclure le chemin de groupe
            excludeGroupPathExact: Exclure le chemin de groupe exact
            jobExactFilter: Nom exact du job
            excludeJobExactFilter: Exclure le nom exact du job
            max: Nombre maximum de résultats
            offset: Offset de pagination

        Returns:
            Liste d'exécutions
        """
        path = f"/project/{project}/executions"

        params: dict[str, Any] = {}
        if statusFilter:
            params["statusFilter"] = statusFilter
        if abortedbyFilter:
            params["abortedbyFilter"] = abortedbyFilter
        if userFilter:
            params["userFilter"] = userFilter
        if recentFilter:
            params["recentFilter"] = recentFilter
        if olderFilter:
            params["olderFilter"] = olderFilter
        if begin:
            params["begin"] = begin
        if end:
            params["end"] = end
        if adhoc is not None:
            params["adhoc"] = "true" if adhoc else "false"
        if jobIdListFilter:
            params["jobIdListFilter"] = ",".join(jobIdListFilter)
        if excludeJobIdListFilter:
            params["excludeJobIdListFilter"] = ",".join(excludeJobIdListFilter)
        if jobListFilter:
            params["jobListFilter"] = ",".join(jobListFilter)
        if excludeJobListFilter:
            params["excludeJobListFilter"] = ",".join(excludeJobListFilter)
        if groupPath:
            params["groupPath"] = groupPath
        if groupPathExact:
            params["groupPathExact"] = groupPathExact
        if excludeGroupPath:
            params["excludeGroupPath"] = excludeGroupPath
        if excludeGroupPathExact:
            params["excludeGroupPathExact"] = excludeGroupPathExact
        if jobExactFilter:
            params["jobExactFilter"] = jobExactFilter
        if excludeJobExactFilter:
            params["excludeJobExactFilter"] = excludeJobExactFilter
        if max:
            params["max"] = max
        if offset:
            params["offset"] = offset

        result = self.rd.http_list(path, params=params)
        return [self._obj_cls(self, item) for item in result]
