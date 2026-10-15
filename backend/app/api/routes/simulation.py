"""Controlled local traffic simulator endpoints."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.schemas.demo import SimulationRequest, SimulationResponse
from app.services import simulation as sim_service

router = APIRouter(prefix="/simulation", tags=["simulation"])


class SimulationStartRequest(SimulationRequest):
    """Simulation parameters. Target is always the local API — never client-supplied."""

    pass


class CancelResponse(BaseModel):
    cancelled: bool
    message: str


@router.post("/run", response_model=SimulationResponse)
async def run_simulation(
    body: SimulationStartRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> SimulationResponse:
    """Run a controlled simulation against this local BotShield Lab instance.

    The target URL is derived from the incoming request host and restricted
    to SIMULATION_ALLOWED_HOST. Arbitrary remote URLs are rejected.
    """
    # Never accept client-supplied target URLs. Always target this local instance.
    # Use a canonical local base URL for allowlist checks; requests are executed
    # in-process via ASGI so TestClient and production share the same code path.
    base_url = "http://127.0.0.1:8000"

    clamped = body.model_copy(
        update={
            "request_count": min(body.request_count, settings.simulation_max_requests),
            "interval_ms": max(body.interval_ms, settings.simulation_min_interval_ms),
        }
    )
    return await sim_service.run_simulation(
        clamped,
        base_url=base_url,
        settings=settings,
        asgi_app=request.app,
    )



@router.post("/cancel", response_model=CancelResponse)
def cancel_simulation() -> CancelResponse:
    """Request cancellation of an in-progress simulation."""
    sim_service.request_cancel()
    return CancelResponse(cancelled=True, message="Cancel requested.")


class SimulationLimitsOut(BaseModel):
    max_requests: int
    min_interval_ms: int
    allowed_hosts: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


@router.get("/limits", response_model=SimulationLimitsOut)
def simulation_limits(settings: Settings = Depends(get_settings)) -> SimulationLimitsOut:
    return SimulationLimitsOut(
        max_requests=settings.simulation_max_requests,
        min_interval_ms=settings.simulation_min_interval_ms,
        allowed_hosts=settings.simulation_allowed_hosts,
        notes=[
            "Simulator only targets the local BotShield Lab backend.",
            "Arbitrary URLs, proxies, CAPTCHA bypass, and stealth automation are not supported.",
            "Use this tool to demonstrate defensive controls, not to attack third-party sites.",
        ],
    )
