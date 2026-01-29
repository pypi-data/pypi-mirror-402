"""
Myra EU Captcha - Python Bindings
Copyright (c) 2026 Myra Security GmbH
See LICENSE for license.
"""

from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class MyraEuCaptchaResult:
    success: bool
    errors: list[str]

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "MyraEuCaptchaResult":
        return cls(
            success=payload.get("success", False),
            errors=payload.get("errors", []),
        )
