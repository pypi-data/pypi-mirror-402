"""
Gestion des system features (/feature).
"""

from rundeck.base import RundeckObject, RundeckObjectManager


class Feature(RundeckObject):
    """Représente un feature flag système."""

    _id_attr = "name"
    _repr_attr = "name"


class FeatureManager(RundeckObjectManager[Feature]):
    """Manager pour interroger les features système."""

    _path = "/feature"
    _obj_cls = Feature

    def list(self) -> list[Feature]:
        """Liste le statut de tous les features système."""
        base = self._build_path()
        path = f"{base.rstrip('/')}/"
        result = self.rd.http_get(path)
        items = []
        if isinstance(result, dict):
            for name, value in result.items():
                if isinstance(value, dict):
                    items.append({"name": name, **(value or {})})
                else:
                    items.append({"name": name, "enabled": bool(value)})
        return self._wrap_list(items)

    def get(self, name: str) -> Feature:
        """Récupère le statut d'un feature spécifique."""
        path = self._build_path(name)
        data = self.rd.http_get(path)
        if isinstance(data, dict):
            data.setdefault("name", name)
        return self._wrap(data)


__all__ = ["Feature", "FeatureManager"]
