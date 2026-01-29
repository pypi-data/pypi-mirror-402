"""import package"""
from typing import Dict, Optional
import requests

from cubesdk.helper import normalize_secret_key
from .constant import DEFAULT_BASE_URL, SDK_VERSION, DEFAULT_API_VERSION
from .cache import TTLCache
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    SecretNotFoundError,
    APIError,
)


class CubeSDK:
    """CubeSDK Class"""
    def __init__(
        self,
        service_token: str,
        api_version: str = DEFAULT_API_VERSION,
        default_env: str = "development",
        base_url: Optional[str] = None,
        timeout: int = 5,
        cache_ttl: int = 60,
    ):
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.api_version = api_version
        self.service_token = service_token
        self.default_env = default_env
        self.timeout = timeout
        self.cache = TTLCache(cache_ttl)

        self.headers = {
            "Authorization": f"Bearer {self.service_token}",
            "X-SDK-Version": SDK_VERSION,
            "X-Environment": self.default_env,
            "Content-Type": "application/json",
        }

    def __repr__(self) -> str:
        return (
            f"CubeSDK("
            f"env={self.default_env!r}, "
            f"base_url={self.base_url!r}, "
            f"api_version={self.api_version!r}"
            f")"
        )

    # -------------------------
    # URL Builder
    # -------------------------


    def _url(self, path: str) -> str:
        return f"{self.base_url}/v1{path}"

    # -------------------------
    # Secrets
    # -------------------------

    def get_secret(self, key: str) -> str:
        """Get Secret Func"""
        normalized_key = normalize_secret_key(key)
        cache_key = f"{self.default_env}:{normalized_key}"

        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        value = self.fetch_secret(normalized_key)
        self.cache.set(cache_key, value)
        return value

    def get_secrets(self) -> Dict[str, str]:
        """Get Secrets Func"""
        url = self._url("/sdk/secrets")

        response = requests.get(
            url,
            headers=self.headers,
            timeout=self.timeout,
        )

        # 🔥 LIST ENDPOINT MUST NOT THROW
        if response.status_code == 404:
            return {}

        self._handle_errors(response)

        result: Dict[str, str] = {}
        for item in response.json():
            normalized_key = normalize_secret_key(item["key"])
            result[normalized_key] = item["value"]
            self.cache.set(
                f"{self.default_env}:{normalized_key}",
                item["value"],
            )

        return result

    def fetch_secret(self, key: str) -> str:
        """Fetch Secret Func"""
        normalized_key = normalize_secret_key(key)

        url = self._url(f"/sdk/secrets/{normalized_key}")

        response = requests.get(
            url,
            headers=self.headers,
            timeout=self.timeout,
        )

        self._handle_errors(response)

        data = response.json()
        if "value" not in data:
            raise APIError("Malformed API response: missing 'value'")

        return data["value"]

    def switch_env(self, env: str) -> None:
        """Switch ENV Func"""
        self.default_env = env
        self.headers["X-Environment"] = env
        self.cache.clear()

    def refresh(self) -> None:
        """Refresh Func"""
        self.cache.clear()

    def _handle_errors(self, response: requests.Response) -> None:
        if response.status_code == 401:
            raise AuthenticationError("Invalid or expired service token")

        if response.status_code == 403:
            raise AuthorizationError(
                f"Access denied for environment '{self.default_env}'"
            )

        if response.status_code == 404 and "/sdk/secrets/" in response.url:
            raise SecretNotFoundError(
                f"Secret not found in environment '{self.default_env}'")

        if not response.ok:
            raise APIError(
                f"API error {response.status_code}: {response.text}"
            )
