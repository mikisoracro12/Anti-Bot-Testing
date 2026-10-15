"""CAPTCHA verification — Cloudflare Turnstile + explicit local mock.

Never treat a client-side success message as proof of verification.
Secret keys stay on the backend only.
Mock provider must be explicitly enabled and is blocked in production.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import httpx

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass
class CaptchaResult:
    success: bool
    provider: str
    error_codes: list[str] = field(default_factory=list)
    message: str = ""


class CaptchaService:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()

    @property
    def enabled(self) -> bool:
        return self.settings.captcha_enabled

    def status_payload(self) -> dict:
        """Non-sensitive CAPTCHA status for the dashboard."""
        warnings: list[str] = []
        provider = self.settings.captcha_provider
        mock_on = self.settings.captcha_mock_enabled and provider == "mock"
        site_configured = bool(self.settings.turnstile_site_key)
        secret_configured = bool(self.settings.turnstile_secret_key)

        if self.settings.is_production and provider == "mock":
            warnings.append("Mock CAPTCHA must not be used in production.")
        if self.enabled and provider == "turnstile" and not secret_configured:
            warnings.append("TURNSTILE_SECRET_KEY is not configured.")
        if self.enabled and provider == "turnstile" and not site_configured:
            warnings.append("TURNSTILE_SITE_KEY is not configured.")
        if not self.enabled:
            warnings.append("CAPTCHA verification is disabled.")

        ready = False
        if self.enabled:
            if provider == "mock" and mock_on and not self.settings.is_production:
                ready = True
            elif provider == "turnstile" and site_configured and secret_configured:
                ready = True

        return {
            "enabled": self.enabled,
            "provider": provider,
            "site_key_configured": site_configured,
            "secret_configured": secret_configured,
            "mock_enabled": mock_on,
            "site_key": self.settings.turnstile_site_key or None,
            "ready": ready,
            "warnings": warnings,
        }

    async def verify(
        self, token: Optional[str], remote_ip: Optional[str] = None
    ) -> CaptchaResult:
        if not token or not token.strip():
            return CaptchaResult(
                success=False,
                provider=self.settings.captcha_provider,
                error_codes=["missing-input-response"],
                message="CAPTCHA token is missing.",
            )

        provider = self.settings.captcha_provider
        if provider == "mock":
            return self._verify_mock(token)
        return await self._verify_turnstile(token, remote_ip)

    def _verify_mock(self, token: str) -> CaptchaResult:
        if self.settings.is_production:
            logger.error("Attempted mock CAPTCHA verification in production")
            return CaptchaResult(
                success=False,
                provider="mock",
                error_codes=["mock-forbidden-in-production"],
                message="Mock CAPTCHA is forbidden in production.",
            )
        if not self.settings.captcha_mock_enabled:
            return CaptchaResult(
                success=False,
                provider="mock",
                error_codes=["mock-disabled"],
                message="Mock CAPTCHA is not enabled.",
            )
        if token == self.settings.captcha_mock_valid_token:
            return CaptchaResult(
                success=True,
                provider="mock",
                message="Mock CAPTCHA verified.",
            )
        return CaptchaResult(
            success=False,
            provider="mock",
            error_codes=["invalid-input-response"],
            message="Invalid mock CAPTCHA token.",
        )

    async def _verify_turnstile(
        self, token: str, remote_ip: Optional[str]
    ) -> CaptchaResult:
        secret = self.settings.turnstile_secret_key
        if not secret:
            return CaptchaResult(
                success=False,
                provider="turnstile",
                error_codes=["missing-secret"],
                message="Turnstile secret key is not configured.",
            )

        payload = {"secret": secret, "response": token}
        if remote_ip:
            payload["remoteip"] = remote_ip

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.settings.turnstile_verify_url, data=payload
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            logger.warning("Turnstile verification service failure: %s", exc)
            return CaptchaResult(
                success=False,
                provider="turnstile",
                error_codes=["verification-service-failure"],
                message="CAPTCHA verification service unavailable.",
            )

        success = bool(data.get("success"))
        error_codes = list(data.get("error-codes") or [])
        if success:
            return CaptchaResult(
                success=True,
                provider="turnstile",
                message="CAPTCHA verified.",
            )
        return CaptchaResult(
            success=False,
            provider="turnstile",
            error_codes=error_codes,
            message="CAPTCHA verification failed.",
        )


_captcha: Optional[CaptchaService] = None


def get_captcha_service() -> CaptchaService:
    global _captcha
    if _captcha is None:
        _captcha = CaptchaService()
    return _captcha


def reset_captcha_service(settings: Optional[Settings] = None) -> CaptchaService:
    global _captcha
    _captcha = CaptchaService(settings)
    return _captcha
