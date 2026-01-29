"""
Myra EU Captcha - Python Bindings
Copyright (c) 2026 Myra Security GmbH
See LICENSE for license.
"""
import httpx
from typing import Any
from .config import MyraEuCaptchaClientConfig
from .models import MyraEuCaptchaResult
from .exceptions import ConfigurationError, map_httpx_exception

class MyraEuCaptchaClient:
    """Captcha Client for Myra EU Captcha."""

    def __init__(self, config: MyraEuCaptchaClientConfig):
        """ Myra EU Captcha Client.
        Handles server-side verification of Myra EU Captcha tokens. Supports
        optional backend failure suppression and configurable timeouts.

        Attributes:
            config (MyraEuCaptchaClientConfig): Client configuration
        """
        self._config: MyraEuCaptchaClientConfig = config
        if not self._config.sitekey:
            raise ConfigurationError("missing-sitekey")

        if not self._config.secret:
            raise ConfigurationError("missing-secret")

        self._timeout = httpx.Timeout(
            connect=self._config.connect_timeout,
            read=self._config.read_timeout,
            write=self._config.write_timeout,
            pool=self._config.pool_timeout,
        )
        self._async_client = httpx.AsyncClient(timeout=self._timeout)

    def _build_request_data(self, token: str, remote_addr: str) -> dict[str, str]:
        return {
            "sitekey": self._config.sitekey,
            "secret": self._config.secret,
            "remote": remote_addr,
            "response": token,
        }

    def _process_response(self, response: dict[str, Any]) -> MyraEuCaptchaResult:
        if not response["success"]:
            response["errors"] = ["invalid-token"]
        return MyraEuCaptchaResult.from_api(response)

    def _handle_exception(self, exc: Exception) -> MyraEuCaptchaResult:
        mapped = map_httpx_exception(exc)
        if self._config.suppress_exceptions:
            return MyraEuCaptchaResult.from_api({
                "success": self._config.default_result_on_error,
                "errors": [str(mapped)],
            })
        raise mapped

    def _parse_json(self, resp: httpx.Response) -> dict[str, Any]:
        response: dict[str, Any] = resp.json()
        assert "success" in response, "malformed-json-response"
        return response

    async def avalidate(self, token: str = "", remote_addr: str = "") -> MyraEuCaptchaResult:
        """Asynchronous interface to validate an eu-captcha-token response."""
        if not token:
            return MyraEuCaptchaResult.from_api({"errors": ["missing-token"]})

        try:
            resp = await self._async_client.post(
                self._config.verify_url,
                json=self._build_request_data(token, remote_addr),
            )
            return self._process_response(self._parse_json(resp))
        except Exception as exc:
            return self._handle_exception(exc)

    def validate(self, token: str = "", remote_addr: str = "") -> MyraEuCaptchaResult:
        """Synchronous interface to validate an eu-captcha-token response."""
        if not token:
            return MyraEuCaptchaResult.from_api({"errors": ["missing-token"]})

        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(
                    self._config.verify_url,
                    json=self._build_request_data(token, remote_addr),
                )
                return self._process_response(self._parse_json(resp))
        except Exception as exc:
            return self._handle_exception(exc)
