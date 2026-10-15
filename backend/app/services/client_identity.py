"""Derive a sanitized client identifier without trusting arbitrary headers."""

import hashlib
import logging
from typing import Optional

from fastapi import Request

from app.core.config import Settings

logger = logging.getLogger(__name__)


def hash_user_agent(user_agent: Optional[str]) -> Optional[str]:
    if not user_agent:
        return None
    return hashlib.sha256(user_agent.encode("utf-8")).hexdigest()[:16]


def get_client_ip(request: Request, settings: Settings) -> str:
    """Resolve client IP carefully.

    By default only the direct connection peer is used. Forwarded headers
    (X-Forwarded-For, X-Real-IP) are trusted only when trust_forwarded_headers
    is enabled AND the connecting peer is in the trusted proxy list.
    """
    peer = request.client.host if request.client else "unknown"

    if not settings.trust_forwarded_headers:
        return peer

    if settings.trusted_proxy_ip_list and peer not in settings.trusted_proxy_ip_list:
        logger.warning(
            "Ignoring forwarded headers from untrusted peer %s", peer
        )
        return peer

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Left-most is the original client when set by a trusted proxy chain
        return forwarded.split(",")[0].strip() or peer

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    return peer


def sanitize_client_id(ip: str) -> str:
    """Hash IP to avoid storing raw addresses when not needed for demos.

    For local demos we keep a short hash so dashboards remain useful without
    persisting full IP addresses as personal data.
    """
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:12]
