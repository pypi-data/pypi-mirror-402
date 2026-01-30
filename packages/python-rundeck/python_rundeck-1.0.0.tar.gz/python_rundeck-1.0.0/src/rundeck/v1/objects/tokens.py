"""
Gestion des tokens Rundeck
"""

from typing import Any

from rundeck.base import RundeckObject, RundeckObjectManager


class Token(RundeckObject):
    """Représente un token API Rundeck"""

    _id_attr = "id"
    _repr_attr = "user"

    def delete(self) -> None:
        """Supprime le token"""
        self.manager.delete(self.id)


class TokenManager(RundeckObjectManager):
    """Manager pour les tokens"""

    _path = "/tokens"
    _obj_cls = Token

    _single_path = "/token/{id}"

    def _token_path(self, token_id: str) -> str:
        """
        Chemin pour un token unitaire (/token/{id}).
        L'API Rundeck mélange /tokens (collection) et /token/{id} (single),
        on centralise ici pour rester cohérent.
        """
        return self._single_path.format(id=token_id)

    def list(self, user: str | None = None) -> "list[Token]":
        """
        Liste les tokens

        Args:
            user: Filtre par utilisateur

        Returns:
            Liste de tokens
        """
        path = self._build_path(user) if user else self._build_path()
        return self._list(path=path)

    def get(self, token_id: str) -> Token:
        """
        Récupère un token par son ID

        Args:
            token_id: ID du token

        Returns:
            Token
        """
        path = self._token_path(token_id)
        return self._get(token_id, path=path)

    def create(
        self,
        user: str,
        roles: "list[str]",
        duration: str | None = None,
        name: str | None = None,
    ) -> Token:
        """
        Crée un nouveau token

        Args:
            user: Nom d'utilisateur
            roles: Liste des rôles
            duration: Durée de validité (ex: "120d")
            name: Nom du token (API v37+)

        Returns:
            Token créé
        """
        data: dict[str, Any] = {
            "user": user,
            "roles": roles,
        }
        if duration:
            data["duration"] = duration
        if name:
            data["name"] = name

        path = self._build_path(user)
        return self._create(json=data, path=path)

    def delete(self, token_id: str) -> None:
        """
        Supprime un token

        Args:
            token_id: ID du token
        """
        path = self._token_path(token_id)
        self._delete(token_id, path=path)
