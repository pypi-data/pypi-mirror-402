"""
Gestion des plugins installés (/plugin/list).
"""

from rundeck.base import RundeckObject, RundeckObjectManager


class Plugin(RundeckObject):
    """Représente un plugin Rundeck installé."""

    _id_attr = "id"
    _repr_attr = "name"


class PluginManager(RundeckObjectManager[Plugin]):
    """Manager pour lister les plugins installés."""

    _path = "/plugin"
    _obj_cls = Plugin

    def list(self) -> list[Plugin]:
        """Liste les plugins installés sur l'instance."""
        path = self._build_path("list")
        return self._list(path=path)

    def detail(self, service: str, provider: str) -> Plugin:
        """Détails d'un plugin spécifique (service/provider)."""
        path = self._build_path(f"detail/{service}/{provider}")
        result = self.rd.http_get(path)
        # Certains retours ne contiennent pas le champ service ; on le re-injecte
        # pour cohérence.
        if isinstance(result, dict):
            result.setdefault("service", service)
            result.setdefault("provider", provider)
        return self._wrap(result)


__all__ = ["Plugin", "PluginManager"]
