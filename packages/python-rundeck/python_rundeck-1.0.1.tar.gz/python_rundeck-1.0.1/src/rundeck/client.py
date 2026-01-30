from __future__ import annotations

"""
Client principal pour l'API Rundeck
"""

from typing import Any
from urllib.parse import urljoin

import requests

from rundeck.config import RundeckConfig
from rundeck.const import (
    HTTP_DELETE,
    HTTP_GET,
    HTTP_POST,
    HTTP_PUT,
    RUNDECK_AUTH_HEADER,
)
from rundeck.exceptions import (
    RundeckAuthenticationError,
    RundeckConnectionError,
    RundeckTimeoutError,
    raise_for_status,
)


class Rundeck:
    """Wrapper pour interagir avec l'API Rundeck."""

    def __init__(
        self,
        url: str | None = None,
        token: str | None = None,
        username: str | None = None,
        password: str | None = None,
        api_version: int | None = None,
        timeout: float | None = None,
        ssl_verify: bool | None = None,
        session: requests.Session | None = None,
        config_files: list[str] | None = None,
    ) -> None:
        self.config = RundeckConfig(
            url=url,
            token=token,
            username=username,
            password=password,
            api_version=api_version,
            timeout=timeout,
            ssl_verify=ssl_verify,
            config_files=config_files,
        )

        if not self.config.url:
            raise ValueError("URL Rundeck manquante (config ou argument requis).")

        self._base_url = self.config.url.rstrip("/")
        self._api_version = str(self.config.api_version)
        self._api_url = f"{self._base_url}/api/{self._api_version}"

        self.timeout = self.config.timeout
        self.ssl_verify = self.config.ssl_verify

        self.session = session or requests.Session()
        self.headers = {
            "User-Agent": getattr(self.config, "user_agent", None) or "python-rundeck",
            "Accept": "application/json",
        }
        if self.config.token:
            self.headers[RUNDECK_AUTH_HEADER] = self.config.token
        self.session.headers.update(self.headers)
        self.session.verify = self.ssl_verify

        if not self.config.token and self.config.username and self.config.password:
            self._authenticate_with_password()

        self._init_managers()

    def _init_managers(self) -> None:
        """Initialise les managers d'objets."""
        # Import paresseux pour éviter les boucles d'import.
        from rundeck.v1.objects.config_management import ConfigManagementManager
        from rundeck.v1.objects.executions import ExecutionManager
        from rundeck.v1.objects.features import FeatureManager
        from rundeck.v1.objects.jobs import JobManager
        from rundeck.v1.objects.key_storage import StorageKeyManager
        from rundeck.v1.objects.metrics import MetricsManager
        from rundeck.v1.objects.plugins import PluginManager
        from rundeck.v1.objects.projects import ProjectManager
        from rundeck.v1.objects.scheduler import SchedulerManager
        from rundeck.v1.objects.system import SystemManager
        from rundeck.v1.objects.tokens import TokenManager
        from rundeck.v1.objects.users import UserManager
        from rundeck.v1.objects.webhooks import WebhookEventManager

        self.projects = ProjectManager(self)
        self.jobs = JobManager(self)
        self.executions = ExecutionManager(self)
        self.config_management = ConfigManagementManager(self)
        self.metrics = MetricsManager(self)
        self.plugins = PluginManager(self)
        self.webhooks = WebhookEventManager(self)
        self.key_storage = StorageKeyManager(self)
        self.features = FeatureManager(self)
        self.system = SystemManager(self)
        self.scheduler = SchedulerManager(self)
        self.tokens = TokenManager(self)
        self.users = UserManager(self)

    @property
    def url(self) -> str:
        """URL fournie par l'utilisateur."""
        return self._base_url

    @property
    def api_url(self) -> str:
        """URL de base de l'API."""
        return self._api_url

    @property
    def api_version(self) -> str:
        """Version de l'API utilisée."""
        return self._api_version

    @classmethod
    def from_config(
        cls,
        config_section: str | None = None,
        config_files: list[str] | None = None,
        **kwargs: Any,
    ) -> "Rundeck":
        """
        Construit un client Rundeck à partir des fichiers de configuration/env.
        """
        conf = RundeckConfig(
            config_files=config_files,
            config_section=config_section or "rundeck",
        )
        return cls(
            url=conf.url,
            token=conf.token,
            username=conf.username,
            password=conf.password,
            api_version=conf.api_version,
            timeout=conf.timeout,
            ssl_verify=conf.ssl_verify,
            session=kwargs.get("session"),
            config_files=config_files,
        )

    def _authenticate_with_password(self) -> None:
        """Authentification via j_security_check + cookie de session."""
        login_url = urljoin(f"{self._base_url}/", "j_security_check")
        try:
            response = self.session.post(
                login_url,
                data={
                    "j_username": self.config.username,
                    "j_password": self.config.password,
                },
                allow_redirects=True,
                timeout=self.timeout,
                verify=self.ssl_verify,
                headers={
                    "Accept": "application/json",
                    "User-Agent": self.headers.get("User-Agent", "python-rundeck"),
                },
            )
        except requests.exceptions.Timeout as exc:
            raise RundeckTimeoutError(
                f"Timeout lors de l'authentification: {exc}"
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise RundeckConnectionError(
                f"Erreur de connexion lors de l'authentification: {exc}"
            ) from exc

        urls = [response.url] + [r.url for r in response.history]
        if any("/user/login" in (u or "") or "/user/error" in (u or "") for u in urls):
            raise RundeckAuthenticationError(
                "Authentification échouée (login/error)", None, response
            )
        if response.status_code >= 400:
            raise RundeckAuthenticationError(
                f"Authentification échouée (HTTP {response.status_code})",
                None,
                response,
            )

        cookies = self.session.cookies.get_dict()
        if "JSESSIONID" not in cookies:
            raise RundeckAuthenticationError(
                "Cookie de session JSESSIONID manquant après authentification",
                None,
                response,
            )

    def _make_request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        data: Any = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        files: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        if headers:
            request_headers = self.session.headers.copy()
            request_headers.update(headers)
        else:
            request_headers = None

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json,
                files=files,
                headers=request_headers,
                timeout=self.timeout,
                verify=self.ssl_verify,
                **kwargs,
            )
            raise_for_status(response)
            return response
        except requests.exceptions.Timeout as exc:
            raise RundeckTimeoutError(f"Timeout lors de la requête: {exc}") from exc
        except requests.exceptions.ConnectionError as exc:
            raise RundeckConnectionError(f"Erreur de connexion: {exc}") from exc

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        data: Any = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        files: dict[str, Any] | None = None,
        raw: bool = False,
        **kwargs: Any,
    ) -> Any:
        """
        Effectue une requête sur le chemin donné et retourne le contenu déjà parsé.
        """
        url = path
        if not path.startswith("http"):
            url = urljoin(f"{self.api_url}/", path.lstrip("/"))

        response = self._make_request(
            method=method,
            url=url,
            params=params,
            data=data,
            json=json,
            headers=headers,
            files=files,
            **kwargs,
        )

        if raw:
            return response

        if method == HTTP_DELETE:
            return None
        if response.text:
            try:
                return response.json()
            except ValueError:
                return response.text
        return {}

    def http_get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        raw: bool = False,
        **kwargs: Any,
    ) -> Any:
        return self._request(HTTP_GET, url, params=params, raw=raw, **kwargs)

    def http_list(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[Any]:
        result = self.http_get(url, params=params, **kwargs)

        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            for key in ["items", "data", "results", "executions", "jobs", "projects"]:
                if key in result and isinstance(result[key], list):
                    return result[key]
            return [result] if result else []
        return []

    def http_post(
        self,
        url: str,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        raw: bool = False,
        **kwargs: Any,
    ) -> Any:
        return self._request(
            HTTP_POST, url, data=data, json=json, files=files, raw=raw, **kwargs
        )

    def http_put(
        self,
        url: str,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        raw: bool = False,
        **kwargs: Any,
    ) -> Any:
        return self._request(
            HTTP_PUT, url, data=data, json=json, files=files, raw=raw, **kwargs
        )

    def http_delete(
        self,
        url: str,
        raw: bool = False,
        **kwargs: Any,
    ) -> None:
        self._request(HTTP_DELETE, url, raw=raw, **kwargs)

    def __enter__(self) -> "Rundeck":
        return self

    def __exit__(self, *args: Any) -> None:
        self.session.close()
