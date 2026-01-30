"""
Gestion du stockage des clés (/storage/keys).
"""

from __future__ import annotations

from typing import Any

from rundeck.base import RundeckObject, RundeckObjectManager


class StorageKey(RundeckObject):
    """Ressource de stockage (fichier ou dossier)."""

    _id_attr = "path"
    _repr_attr = "name"

    def _relative_path(self) -> str:
        path = self.path
        # API returns "keys/..." but endpoints expect the relative path.
        if isinstance(path, str) and path.startswith("keys/"):
            return path[len("keys/") :]
        return path

    def content(self, accept: str = "application/pgp-keys") -> bytes:
        """Récupère le contenu d'une clé (ex: clé publique)."""
        path = self.manager._file_path(self._relative_path())
        headers = {"Accept": accept} if accept else None
        response = self.manager.rd.http_get(path, headers=headers, raw=True)
        return response.content

    def update(self, content: bytes | str, content_type: str) -> dict[str, Any]:
        """Met à jour le contenu de la clé et rafraîchit l'objet."""
        updated = self.manager.update(
            self._relative_path(), content=content, content_type=content_type
        )
        self._attrs = updated._attrs
        return updated.to_dict()


class StorageKeyManager(RundeckObjectManager[StorageKey]):
    """Manager pour les clés/ressources du storage."""

    _path = "/storage/keys"
    _obj_cls = StorageKey

    def _dir_path(self, path: str | None = None) -> str:
        base = self._build_path()
        if path:
            cleaned = path.strip("/")
            return f"{base}/{cleaned}/"
        return base

    def _file_path(self, path: str) -> str:
        base = self._build_path()
        cleaned = path.strip("/")
        return f"{base}/{cleaned}"

    def list(self, path: str | None = None) -> list[StorageKey]:
        """Liste les ressources (fichiers/dossiers) sous le chemin donné."""
        target = self._dir_path(path)
        result = self.rd.http_get(target)
        resources = []
        if isinstance(result, dict):
            resources = result.get("resources") or []
        return self._wrap_list(resources)

    def get(self, path: str) -> StorageKey:
        """Récupère les métadonnées d'une clé/fichier."""
        target = self._file_path(path)
        result = self.rd.http_get(target)
        if isinstance(result, dict):
            return self._wrap(result)
        return self._wrap({"path": path, "raw": result})

    def create(self, path: str, content: bytes | str, content_type: str) -> StorageKey:
        """Crée une nouvelle clé/fichier à l'emplacement donné."""
        target = self._file_path(path)
        headers = {"Content-Type": content_type, "Accept": "application/json"}
        result = self.rd.http_post(target, data=content, headers=headers)
        if isinstance(result, dict):
            return self._wrap(result)
        return self._wrap({"path": path, "raw": result})

    def update(self, path: str, content: bytes | str, content_type: str) -> StorageKey:
        """Met à jour une clé/fichier existant."""
        target = self._file_path(path)
        headers = {"Content-Type": content_type, "Accept": "application/json"}
        result = self.rd.http_put(target, data=content, headers=headers)
        if isinstance(result, dict):
            return self._wrap(result)
        return self._wrap({"path": path, "raw": result})

    def delete(self, path: str) -> None:
        """Supprime une clé/fichier."""
        target = self._file_path(path)
        self.rd.http_delete(target)


__all__ = ["StorageKey", "StorageKeyManager"]
