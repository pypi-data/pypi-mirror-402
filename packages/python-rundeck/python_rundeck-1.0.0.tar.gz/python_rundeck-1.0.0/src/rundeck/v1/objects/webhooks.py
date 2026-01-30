"""
Gestion des webhooks projet et envoi d'événements.
"""

from typing import Any

from rundeck.base import RundeckObject, RundeckObjectManager


class Webhook(RundeckObject):
    """Représente un webhook de projet."""

    _id_attr = "id"
    _repr_attr = "name"


class ProjectWebhookManager(RundeckObjectManager[Webhook]):
    """Manager pour les webhooks d'un projet."""

    _path = "/project/{parent}/webhook"
    _obj_cls = Webhook

    def list(self) -> list[Webhook]:
        """Liste les webhooks d'un projet."""
        if not self.parent:
            raise ValueError("Parent projet requis pour lister les webhooks")
        path = f"/project/{self.parent.id}/webhooks"
        return self._list(path=path)

    def get(self, webhook_id: str | int) -> Webhook:
        """Récupère un webhook par son ID."""
        path = self._build_path(str(webhook_id))
        return self._get(str(webhook_id), path=path)

    def create(self, **data: Any) -> Any:
        """
        Crée un webhook de projet.

        Args:
            data: Champs du webhook (name, user, roles, eventPlugin, config,
                enabled, project...).
        """
        payload = dict(data)
        if self.parent and "project" not in payload:
            payload["project"] = self.parent.id
        path = self._build_path()
        return self.rd.http_post(path, json=payload or None)

    def update(self, webhook_id: str | int, **data: Any) -> Any:
        """Met à jour un webhook de projet."""
        # L'API attend souvent les champs existants (roles, eventPlugin, config,
        # user, project, id).
        current_dict: dict[str, Any] = {}
        try:
            current = self.get(webhook_id)
            current_dict = current.to_dict()
        except Exception:
            current_dict = {}

        payload: dict[str, Any] = {}
        payload.update({k: v for k, v in current_dict.items() if v is not None})
        payload.update({k: v for k, v in data.items() if v is not None})
        payload.setdefault("id", webhook_id)
        if self.parent:
            payload["project"] = self.parent.id

        path = self._build_path(str(webhook_id))
        return self.rd.http_post(path, json=payload or None)

    def delete(self, webhook_id: str | int) -> None:
        """Supprime un webhook de projet."""
        path = self._build_path(str(webhook_id))
        self.rd.http_delete(path)


class WebhookEventManager(RundeckObjectManager):
    """Manager pour envoyer des événements sur un webhook (via auth token)."""

    _path = "/webhook"

    def send(
        self,
        auth_token: str,
        *,
        json: dict[str, Any] | None = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """
        Envoie un payload vers un webhook par son token.

        Args:
            auth_token: Token d'authentification du webhook.
            json: Payload JSON (optionnel).
            data: Payload brut (si json non fourni).
            headers: En-têtes additionnels (facultatif).
        """
        path = self._build_path(auth_token)
        if json is not None:
            return self.rd.http_post(path, json=json, headers=headers)
        return self.rd.http_post(path, data=data, headers=headers)


__all__ = ["Webhook", "ProjectWebhookManager", "WebhookEventManager"]
