"""Controlled traffic simulator — local backend only.

Does not accept arbitrary target URLs, proxies, CAPTCHA bypass, or stealth
automation. Conservative limits prevent accidental high-volume traffic.

Uses ASGI in-process transport so simulation always hits this application
instance (safe for tests and single-process demos).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

from app.core.config import Settings, get_settings
from app.schemas.demo import SimulationRequest, SimulationResponse, SimulationResultItem

logger = logging.getLogger(__name__)

_cancel_requested = False


def request_cancel() -> None:
    global _cancel_requested
    _cancel_requested = True


def clear_cancel() -> None:
    global _cancel_requested
    _cancel_requested = False


def is_cancel_requested() -> bool:
    return _cancel_requested


def validate_base_url(base_url: str, settings: Settings) -> str:
    """Ensure simulation only targets the local BotShield Lab backend."""
    parsed = urlparse(base_url)
    host = (parsed.hostname or "").lower()
    allowed = {h.lower() for h in settings.simulation_allowed_hosts}

    if parsed.scheme not in ("http", "https"):
        raise ValueError("Simulation target must use http or https.")
    if host not in allowed:
        raise ValueError(
            f"Simulation target host '{host}' is not allowed. "
            f"Allowed hosts: {', '.join(sorted(allowed))}."
        )
    if parsed.path and parsed.path not in ("", "/"):
        base_url = f"{parsed.scheme}://{parsed.netloc}"
    return base_url.rstrip("/")


async def run_simulation(
    body: SimulationRequest,
    *,
    base_url: str,
    settings: Optional[Settings] = None,
    asgi_app: Any = None,
) -> SimulationResponse:
    settings = settings or get_settings()
    clear_cancel()

    count = min(body.request_count, settings.simulation_max_requests)
    interval_ms = max(body.interval_ms, settings.simulation_min_interval_ms)

    try:
        base = validate_base_url(base_url, settings)
    except ValueError as exc:
        return SimulationResponse(
            mode=body.mode,
            total=0,
            successful=0,
            rejected=0,
            failed=0,
            results=[],
            message=str(exc),
        )

    path = "/api/v1/demo/protected" if body.endpoint == "demo" else "/api/v1/health"
    url = f"{base}{path}"

    if body.mode == "burst":
        interval_ms = max(settings.simulation_min_interval_ms, min(interval_ms, 100))
    elif body.mode == "normal":
        interval_ms = max(interval_ms, 200)

    results: list[SimulationResultItem] = []
    successful = rejected = failed = 0
    cancelled = False

    headers = {"User-Agent": "BotShieldLab-Simulator/1.0"}
    if body.mode == "repeat":
        headers["User-Agent"] = "python-requests/2.31.0"

    client_kwargs: dict[str, Any] = {"timeout": 10.0}
    if asgi_app is not None:
        client_kwargs["transport"] = httpx.ASGITransport(app=asgi_app)
        client_kwargs["base_url"] = base

    async with httpx.AsyncClient(**client_kwargs) as client:
        for i in range(count):
            if is_cancel_requested():
                cancelled = True
                break

            try:
                if body.endpoint == "demo":
                    resp = await client.post(
                        url if asgi_app is None else path,
                        json={"message": f"sim-{body.mode}-{i}"},
                        headers=headers,
                    )
                else:
                    resp = await client.get(
                        url if asgi_app is None else path,
                        headers=headers,
                    )

                outcome = "allowed"
                risk: float | None = None
                if resp.status_code == 429:
                    outcome = "rate_limited"
                    rejected += 1
                elif resp.status_code >= 400:
                    outcome = "rejected"
                    rejected += 1
                else:
                    successful += 1
                    try:
                        data: dict[str, Any] = resp.json()
                        risk = data.get("risk_score")
                        outcome = data.get("status", "allowed")
                        if outcome != "allowed" and resp.status_code < 400:
                            pass
                    except Exception:  # noqa: BLE001
                        pass

                results.append(
                    SimulationResultItem(
                        index=i,
                        status_code=resp.status_code,
                        outcome=outcome,
                        risk_score=risk,
                    )
                )
            except httpx.HTTPError as exc:
                failed += 1
                results.append(
                    SimulationResultItem(
                        index=i,
                        status_code=0,
                        outcome="failed",
                        error=str(exc),
                    )
                )

            if i < count - 1 and not is_cancel_requested():
                await asyncio.sleep(interval_ms / 1000.0)

    msg = "Simulation cancelled by user." if cancelled else "Simulation completed."

    return SimulationResponse(
        mode=body.mode,
        total=len(results),
        successful=successful,
        rejected=rejected,
        failed=failed,
        cancelled=cancelled,
        results=results,
        message=msg,
    )
