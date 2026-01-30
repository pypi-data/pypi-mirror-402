import json
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import httpx

from philvault_sdk.errors import PhilVaultHTTPError


class AsyncPhilVaultClient:
    """Async HTTP client for PhilVault authentication and authorization APIs."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        access_token: Optional[str] = None,
        timeout: int = 10,
        user_agent: str = "philvault-sdk/0.1.0",
        verify_ssl: bool = True,
        api_key_header: str = "X-API-Key",
        extra_headers: Optional[Dict[str, str]] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        base_url = base_url.strip() if base_url else ""
        api_key = api_key.strip() if api_key else ""

        if not base_url:
            raise ValueError("base_url is required")
        if not api_key:
            raise ValueError("api_key is required")

        self.base_url = base_url.rstrip("/") + "/"
        self.api_key = api_key
        self.access_token = access_token
        self.timeout = timeout
        self.user_agent = user_agent
        self.verify_ssl = verify_ssl
        self.api_key_header = api_key_header
        self.extra_headers = extra_headers or {}
        self.client = client or httpx.AsyncClient(verify=self.verify_ssl)

    async def aclose(self) -> None:
        await self.client.aclose()

    async def __aenter__(self) -> "AsyncPhilVaultClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    @classmethod
    def from_env(
        cls,
        base_url_env: str = "PHILVAULT_BASE_URL",
        api_key_env: str = "PHILVAULT_API_KEY",
        access_token_env: str = "PHILVAULT_ACCESS_TOKEN",
        timeout_env: str = "PHILVAULT_TIMEOUT",
        verify_ssl_env: str = "PHILVAULT_VERIFY_SSL",
        api_key_header_env: str = "PHILVAULT_API_KEY_HEADER",
        user_agent_env: str = "PHILVAULT_USER_AGENT",
    ) -> "AsyncPhilVaultClient":
        """Create client using environment variables with defaults."""
        import os

        base_url = os.getenv(base_url_env, "").strip()
        api_key = os.getenv(api_key_env, "").strip()
        access_token = os.getenv(access_token_env) or None

        timeout_value = os.getenv(timeout_env)
        timeout = int(timeout_value) if timeout_value else 10

        verify_ssl_value = os.getenv(verify_ssl_env)
        if verify_ssl_value is None:
            verify_ssl = True
        else:
            verify_ssl = verify_ssl_value.strip().lower() in {"1", "true", "yes", "on"}

        api_key_header = os.getenv(api_key_header_env) or "X-API-Key"
        user_agent = os.getenv(user_agent_env) or "philvault-sdk/0.1.0"

        return cls(
            base_url=base_url,
            api_key=api_key,
            access_token=access_token,
            timeout=timeout,
            user_agent=user_agent,
            verify_ssl=verify_ssl,
            api_key_header=api_key_header,
        )

    def set_access_token(self, access_token: Optional[str]) -> None:
        """Set or clear the access token used for authenticated endpoints."""
        self.access_token = access_token

    def set_api_key(self, api_key: str) -> None:
        """Update API key used in request headers."""
        api_key = api_key.strip() if api_key else ""
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key

    def _build_url(self, path: str) -> str:
        return urljoin(self.base_url, path.lstrip("/"))

    def _headers(self) -> Dict[str, str]:
        headers = {self.api_key_header: self.api_key, "User-Agent": self.user_agent}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        if self.extra_headers:
            headers.update(self.extra_headers)
        return headers

    async def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        url = self._build_url(path)
        headers = dict(self._headers())
        request_headers = kwargs.pop("headers", None)
        if request_headers:
            headers.update(request_headers)

        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout
        return await self.client.request(
            method=method, url=url, headers=headers, **kwargs
        )

    async def get(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("DELETE", path, **kwargs)

    async def head(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("HEAD", path, **kwargs)

    async def options(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("OPTIONS", path, **kwargs)

    async def _request(
        self,
        method: str,
        path: str,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        response = await self.request(method, path, json=json_body)

        if response.status_code >= 400:
            payload = None
            message = response.text
            try:
                payload = response.json()
                message = json.dumps(payload)
            except ValueError:
                payload = response.text
            raise PhilVaultHTTPError(response.status_code, message, payload=payload)

        if response.status_code == 204:
            return {}

        if response.content:
            return response.json()
        return {}

    # Authentication endpoints
    async def register(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        domain_roles: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "username": username,
            "password": password,
        }
        if email is not None:
            payload["email"] = email
        if domain_roles is not None:
            payload["domain_roles"] = domain_roles
        return await self._request("POST", "/api/v1/auth/register/", payload)

    async def login(self, username: str, password: str) -> Dict[str, Any]:
        payload = {"username": username, "password": password}
        return await self._request("POST", "/api/v1/auth/login/", payload)

    async def refresh(self, refresh_token: str) -> Dict[str, Any]:
        payload = {"refresh_token": refresh_token}
        return await self._request("POST", "/api/v1/auth/refresh/", payload)

    async def me(self) -> Dict[str, Any]:
        return await self._request("GET", "/api/v1/auth/me/")

    async def change_password(
        self, old_password: str, new_password: str
    ) -> Dict[str, Any]:
        payload = {"old_password": old_password, "new_password": new_password}
        return await self._request("POST", "/api/v1/auth/change-password/", payload)

    # ACL endpoints
    async def check_permission(
        self, user_id: str, domain: str, resource_id: str, action: str
    ) -> Dict[str, Any]:
        payload = {
            "user_id": user_id,
            "domain": domain,
            "resource_id": resource_id,
            "action": action,
        }
        return await self._request("POST", "/api/v1/auth/acl/enforce:check", payload)

    async def check_permission_batch(self, policies: list) -> Dict[str, Any]:
        payload = {"policies": policies}
        return await self._request(
            "POST", "/api/v1/auth/acl/enforce:batch_check", payload
        )

    async def add_policy(
        self, subject: str, domain: str, object_name: str, action: str
    ) -> Dict[str, Any]:
        payload = {
            "subject": subject,
            "domain": domain,
            "object": object_name,
            "action": action,
        }
        return await self._request("POST", "/api/v1/auth/acl/enforce:add", payload)

    async def revoke_policy(
        self, subject: str, domain: str, object_name: str, action: str
    ) -> Dict[str, Any]:
        payload = {
            "subject": subject,
            "domain": domain,
            "object": object_name,
            "action": action,
        }
        return await self._request("POST", "/api/v1/auth/acl/enforce:revoke", payload)

    async def assign_domain_role(
        self, user_id: str, role: str, domain: str
    ) -> Dict[str, Any]:
        payload = {"user_id": user_id, "role": role, "domain": domain}
        return await self._request("POST", "/api/v1/auth/acl/roles:assign/", payload)

    async def remove_domain_role(
        self, user_id: str, role: str, domain: str
    ) -> Dict[str, Any]:
        payload = {"user_id": user_id, "role": role, "domain": domain}
        return await self._request("POST", "/api/v1/auth/acl/roles:remove/", payload)

    async def list_domain_roles(self, user_id: str, domain: str) -> Dict[str, Any]:
        payload = {"user_id": user_id, "domain": domain}
        return await self._request("POST", "/api/v1/auth/acl/roles:list/", payload)

    async def add_resource_policy(
        self, resource_id: str, parent_resource_id: str
    ) -> Dict[str, Any]:
        payload = {
            "resource_id": resource_id,
            "parent_resource_id": parent_resource_id,
        }
        return await self._request("POST", "/api/v1/auth/acl/resources:assign/", payload)

    async def remove_resource_policy(
        self, resource_id: str, parent_resource_id: str
    ) -> Dict[str, Any]:
        payload = {
            "resource_id": resource_id,
            "parent_resource_id": parent_resource_id,
        }
        return await self._request("POST", "/api/v1/auth/acl/resources:remove/", payload)
