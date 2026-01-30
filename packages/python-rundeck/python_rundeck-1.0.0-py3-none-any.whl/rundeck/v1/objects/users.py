"""
Gestion des utilisateurs Rundeck
"""

from typing import Any

from rundeck.base import RundeckObject, RundeckObjectManager


class User(RundeckObject):
    """Représente un utilisateur Rundeck"""

    _id_attr = "login"
    _repr_attr = "login"

    def update(
        self,
        firstName: str | None = None,
        lastName: str | None = None,
        email: str | None = None,
    ) -> dict[str, Any]:
        """
        Met à jour les informations de l'utilisateur

        Args:
            firstName: Prénom
            lastName: Nom
            email: Email

        Returns:
            Réponse brute de l'API.
        """
        data: dict[str, Any] = {}
        if firstName:
            data["firstName"] = firstName
        if lastName:
            data["lastName"] = lastName
        if email:
            data["email"] = email

        path = self.manager._build_path(f"info/{self.login}")
        result = self.manager.rd.http_post(path, json=data)
        if isinstance(result, dict):
            self._attrs.update(result)
        return result

    def roles(self) -> list[str]:
        """
        Récupère les rôles de l'utilisateur

        Returns:
            Liste des rôles
        """
        path = self.manager._build_path("roles")
        result = self.manager.rd.http_get(path)
        return result.get("roles", [])


class UserManager(RundeckObjectManager):
    """Manager pour les utilisateurs"""

    _path = "/user"
    _obj_cls = User

    def list(self) -> "list[User]":
        """
        Liste tous les utilisateurs

        Returns:
            Liste d'utilisateurs
        """
        path = self._build_path("list")
        return self._list(path=path)

    def get(self, login: str) -> User:
        """
        Récupère un utilisateur par son login

        Args:
            login: Login de l'utilisateur

        Returns:
            Utilisateur
        """
        path = self._build_path(f"info/{login}")
        return self._get(login, path=path)

    def get_current(self) -> User:
        """
        Récupère l'utilisateur courant

        Returns:
            Utilisateur courant
        """
        path = self._build_path("info")
        return self._get("current", path=path)

    def update(
        self,
        login: str,
        firstName: str | None = None,
        lastName: str | None = None,
        email: str | None = None,
    ) -> User:
        """
        Met à jour un utilisateur

        Args:
            login: Login de l'utilisateur
            firstName: Prénom
            lastName: Nom
            email: Email

        Returns:
            Utilisateur mis à jour
        """
        data: dict[str, Any] = {}
        if firstName:
            data["firstName"] = firstName
        if lastName:
            data["lastName"] = lastName
        if email:
            data["email"] = email

        path = self._build_path(f"info/{login}")
        result = self.rd.http_post(path, json=data)
        return self._obj_cls(self, result)

    def current_roles(self) -> "list[str]":
        """
        Récupère les rôles de l'utilisateur courant

        Returns:
            Liste des rôles
        """
        path = self._build_path("roles")
        result = self.rd.http_get(path)
        return result.get("roles", [])
