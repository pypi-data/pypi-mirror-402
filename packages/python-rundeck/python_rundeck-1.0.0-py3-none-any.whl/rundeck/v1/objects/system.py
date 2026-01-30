"""
Gestion du système Rundeck
"""

from typing import Any

from rundeck.base import RundeckObject, RundeckObjectManager


class SystemExecutionsManager(RundeckObjectManager):
    """Sous-manager pour les endpoints executions du système."""

    _path = "/system/executions"

    def enable(self) -> dict[str, Any]:
        """Active le mode d'exécution."""
        path = self._build_path("enable")
        return self.rd.http_post(path)

    def disable(self) -> dict[str, Any]:
        """Désactive le mode d'exécution (mode passif)."""
        path = self._build_path("disable")
        return self.rd.http_post(path)

    def status(self) -> dict[str, Any]:
        """Statut actuel du mode d'exécution."""
        path = self._build_path("status")
        return self.rd.http_get(path)


class SystemACL(RundeckObject):
    """Représente une policy ACL système."""

    _id_attr = "name"
    _repr_attr = "name"

    def update(self, content: str) -> dict[str, Any]:
        """Met à jour la policy ACL et rafraîchit l'objet."""
        updated = self.manager.update(self.name, content)
        self._attrs = updated._attrs
        return updated.to_dict()


class SystemACLManager(RundeckObjectManager[SystemACL]):
    """Sous-manager pour les endpoints ACL système."""

    _path = "/system/acl"
    _obj_cls = SystemACL

    def list(self) -> list[SystemACL]:
        """Liste les politiques ACL système."""
        path = self._build_path("")
        result = self.rd.http_get(path)
        if isinstance(result, dict):
            resources = result.get("resources") or []
            items = []
            for entry in resources:
                name = entry.get("name") or entry.get("path")
                if name:
                    data = dict(entry)
                    data.setdefault("name", name)
                    items.append(data)
            result = items
        return self._wrap_list(result or [])

    def get(self, policy_name: str) -> SystemACL:
        """Récupère une politique ACL (contenu texte)."""
        path = self._build_path(policy_name)
        response = self.rd.http_get(path, raw=True)
        return self._wrap({"name": policy_name, "content": response.text})

    def create(self, policy_name: str, content: str) -> SystemACL:
        """Crée une politique ACL système."""
        path = self._build_path(policy_name)
        headers = {"Content-Type": "application/yaml"}
        result = self.rd.http_post(path, data=content, headers=headers) or {}
        if "name" not in result:
            result["name"] = policy_name
        return self._wrap(result)

    def update(self, policy_name: str, content: str) -> SystemACL:
        """Met à jour une politique ACL système."""
        path = self._build_path(policy_name)
        headers = {"Content-Type": "application/yaml"}
        result = self.rd.http_put(path, data=content, headers=headers) or {}
        if "name" not in result:
            result["name"] = policy_name
        return self._wrap(result)

    def delete(self, policy_name: str) -> None:
        """Supprime une politique ACL système."""
        path = self._build_path(policy_name)
        self.rd.http_delete(path)


class SystemLogStorageManager(RundeckObjectManager):
    """Sous-manager pour les endpoints logstorage du système."""

    _path = "/system/logstorage"

    def info(self) -> dict[str, Any]:
        """Informations sur le stockage des logs."""
        path = self._build_path()
        return self.rd.http_get(path)

    def incomplete(self, max: int = 20, offset: int = 0) -> dict[str, Any]:
        """Liste des exécutions avec stockage incomplet."""
        params = {"max": max, "offset": offset}
        path = self._build_path("incomplete")
        return self.rd.http_get(path, params=params)

    def incomplete_resume(self) -> dict[str, Any]:
        """Reprise du traitement des logs incomplets."""
        path = self._build_path("incomplete/resume")
        return self.rd.http_post(path)


class SystemManager(RundeckObjectManager):
    """Manager pour les opérations système"""

    _path = "/system"

    @property
    def executions(self) -> SystemExecutionsManager:
        """Accès aux endpoints /system/executions/*."""
        return SystemExecutionsManager(self.rd)

    @property
    def acl(self) -> SystemACLManager:
        """Accès aux endpoints ACL système /system/acl/*."""
        return SystemACLManager(self.rd)

    @property
    def logstorage(self) -> SystemLogStorageManager:
        """Accès aux endpoints /system/logstorage/*."""
        return SystemLogStorageManager(self.rd)

    def info(self) -> dict[str, Any]:
        """
        Récupère les informations système

        Returns:
            Informations système
        """
        path = self._build_path("info")
        return self.rd.http_get(path)
