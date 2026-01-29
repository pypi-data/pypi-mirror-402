"""
Myra EU Captcha - Python Bindings
Copyright (c) 2026 Myra Security GmbH
See LICENSE for license.
"""
import httpx

class MyraEuCaptchaError(Exception):
    """Base exception for all Myra EU Captcha errors."""
    pass

class ConfigurationError(MyraEuCaptchaError):
    """invalid-or-missing-configuration"""
    pass

class NetworkError(MyraEuCaptchaError):
    """network-connection-failure"""
    pass

class TimeoutError(MyraEuCaptchaError):
    """timeout"""
    pass

class APIError(MyraEuCaptchaError):
    """remote-api-error"""
    pass

def map_httpx_exception(exc: Exception) -> Exception:
    if isinstance(exc, httpx.ConnectTimeout):
        return TimeoutError("timeout-error-while-connecting")

    if isinstance(exc, httpx.ReadTimeout):
        return TimeoutError("timeout-error-while-reading")

    if isinstance(exc, httpx.NetworkError):
        return NetworkError("network-connection-error")

    if isinstance(exc, httpx.HTTPStatusError):
        return APIError("invalid-statuscode")

    if isinstance(exc, httpx.DecodingError):
        return APIError("invalid-json-response")

    if isinstance(exc, AssertionError):
        return APIError("malformed-json-response")

    return exc
