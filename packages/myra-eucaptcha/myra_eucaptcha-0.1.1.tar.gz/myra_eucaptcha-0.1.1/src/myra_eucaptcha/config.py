"""
Myra EU Captcha - Python Bindings
Copyright (c) 2026 Myra Security GmbH
See LICENSE for license.
"""

from dataclasses import dataclass

@dataclass
class MyraEuCaptchaClientConfig:
    """Main Python binding Configuration for Myra EU Captcha.

    Handles server-side verification of Myra EU Captcha tokens. Supports
    optional backend failure suppression and configurable timeouts.

    Attributes:
        sitekey (str): The public site key used for client-side integration.
        secret (str): The secret key used for server-side verification.
        verify_url (str): The endpoint URL for verifying captcha tokens.
        read_timeout (int): read timeout in seconds, defaults to 10.
        connect_timeout (int): read timeout in seconds, defaults to 3.
        default_result_on_error (bool): Fallback value if verification cannot be completed. Default 'True'.
        suppress_exceptions (bool): If True, backend exceptions are caught and
            converted to a failed verification instead of raising errors.
    """
    sitekey: str
    secret: str
    verify_url: str = "https://api.eu-captcha.eu/v1/verify/"
    connect_timeout: int = 3
    read_timeout: int = 10
    write_timeout: int = 10
    pool_timeout: int = 3
    default_result_on_error:bool = True
    suppress_exceptions:bool = True
