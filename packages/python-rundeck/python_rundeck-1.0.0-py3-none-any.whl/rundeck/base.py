from __future__ import annotations

"""
Bases objet/manager alignées sur le pattern python-gitlab,
adossées au client `_request`.
"""

import pprint as _pprint
from typing import Any, Generic, Iterable, Iterator, TypeVar

from rundeck.const import HTTP_DELETE, HTTP_GET, HTTP_POST, HTTP_PUT

ResourceT = TypeVar("ResourceT", bound="RundeckObject")


class RundeckObject(Generic[ResourceT]):
    """Objet de base représentant une ressource Rundeck."""

    _id_attr: str = "id"
    _repr_attr: str | None = None

    def __init__(
        self,
        manager: "RundeckObjectManager[ResourceT]",
        attrs: dict[str, Any],
    ) -> None:
        self.manager = manager
        self.rd = manager.rd
        self._attrs = attrs or {}

    def __getattr__(self, name: str) -> Any:
        try:
            return self._attrs[name]
        except KeyError:
            raise AttributeError(name) from None

    def __repr__(self) -> str:
        value = None
        if self._repr_attr and self._repr_attr in self._attrs:
            value = self._attrs[self._repr_attr]
        elif self._id_attr in self._attrs:
            value = self._attrs[self._id_attr]
        suffix = f" {value}" if value is not None else ""
        return f"<{self.__class__.__name__}{suffix}>"

    @property
    def id(self) -> Any:
        return self._attrs.get(self._id_attr)

    def to_dict(self) -> dict[str, Any]:
        return dict(self._attrs)

    def refresh(self: ResourceT) -> None:
        """
        Recharge la ressource en interrogeant son manager.

        """
        ident = self._attrs.get(self._id_attr)
        if ident is None:
            raise AttributeError(f"{self.__class__.__name__} has no identifier")
        fresh = self.manager.get(ident)
        self._attrs = fresh._attrs

    def pformat(self) -> str:
        """Retourne une représentation jolie du dictionnaire d'attributs."""
        return _pprint.pformat(self.to_dict())

    def pprint(self) -> None:
        """Affiche la représentation jolie des attributs."""
        _pprint.pprint(self.to_dict())


class RundeckObjectManager(Generic[ResourceT]):
    """Manager de base fournissant helpers CRUD et wrapping."""

    _path: str = ""
    _obj_cls: type[ResourceT] = RundeckObject  # type: ignore[assignment]

    def __init__(self, rd: Any, parent: RundeckObject | None = None) -> None:
        self.rd = rd
        self.parent = parent

    def _base_path(self) -> str:
        base = self._path or ""
        if "{parent}" in base:
            if not self.parent:
                raise ValueError("Parent requis pour ce manager")
            base = base.format(parent=self.parent.id)
        elif (
            base
            and not base.startswith("/")
            and self.parent
            and getattr(self.parent, "manager", None)
        ):
            # Cascade automatique : si _path est relatif, préfixer avec le chemin
            # du manager parent.
            parent_path = self.parent.manager._build_path(
                getattr(self.parent, getattr(self.parent, "_id_attr", "id"), None)
            )
            base = (
                f"{parent_path.rstrip('/')}/{base.lstrip('/')}" if base else parent_path
            )
        return base

    def _build_path(self, suffix: str | None = None) -> str:
        base = self._base_path()
        if suffix:
            if base.endswith("/"):
                return f"{base}{suffix.lstrip('/')}"
            if base:
                return f"{base}/{suffix.lstrip('/')}"
            return suffix
        return base

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> Any:
        return self.rd._request(
            method=method,
            path=path,
            params=params,
            json=json,
            data=data,
            headers=headers,
            **kwargs,
        )

    def _wrap(self, data: dict[str, Any]) -> ResourceT:
        return self._obj_cls(self, data)

    def _wrap_list(self, items: Iterable[dict[str, Any]]) -> list[ResourceT]:
        return [self._wrap(item) for item in items]

    def iter(
        self,
        path: str | None = None,
        params: dict[str, Any] | None = None,
        page_size: int | None = None,
        **kwargs: Any,
    ) -> Iterator[ResourceT]:
        """
        Générateur paginé sur les ressources (offset/max).
        """
        target = path or self._build_path()
        query: dict[str, Any] = dict(params or {})
        offset = int(query.get("offset", 0))
        if page_size:
            query["max"] = page_size

        while True:
            current_params = dict(query)
            current_params["offset"] = offset
            page = self.rd.http_list(target, params=current_params, **kwargs)
            if not page:
                break
            for item in page:
                yield self._wrap(item)
            if page_size and len(page) < page_size:
                break
            offset += len(page)

    def _list(
        self,
        params: dict[str, Any] | None = None,
        path: str | None = None,
        **kwargs: Any,
    ) -> list[ResourceT]:
        target = path or self._build_path()
        result = self.rd.http_list(target, params=params, **kwargs)
        return self._wrap_list(result)

    def _get(
        self,
        ident: str,
        params: dict[str, Any] | None = None,
        path: str | None = None,
        **kwargs: Any,
    ) -> ResourceT:
        target = path or self._build_path(str(ident))
        result = self.rd._request(HTTP_GET, target, params=params, **kwargs)
        return self._wrap(result)

    def _create(
        self,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        path: str | None = None,
        **kwargs: Any,
    ) -> ResourceT:
        target = path or self._build_path()
        result = self.rd._request(
            HTTP_POST, target, json=json, data=data, params=params, **kwargs
        )
        return self._wrap(result)

    def _update(
        self,
        ident: str,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        path: str | None = None,
        **kwargs: Any,
    ) -> ResourceT:
        target = path or self._build_path(str(ident))
        result = self.rd._request(
            HTTP_PUT, target, json=json, data=data, params=params, **kwargs
        )
        return self._wrap(result)

    def _delete(
        self,
        ident: str,
        params: dict[str, Any] | None = None,
        path: str | None = None,
        **kwargs: Any,
    ) -> None:
        target = path or self._build_path(str(ident))
        self.rd._request(HTTP_DELETE, target, params=params, **kwargs)


__all__ = [
    "RundeckObject",
    "RundeckObjectManager",
]
