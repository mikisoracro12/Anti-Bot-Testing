"""Demo protected endpoint exercising rate limits, detection, and CAPTCHA."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.demo import CaptchaVerifyRequest, CaptchaVerifyResponse, DemoRequestBody, DemoResponse
from app.schemas.event import DetectionReason, RequestEventCreate
from app.services.bot_detector import get_bot_detector
from app.services.captcha import get_captcha_service
from app.services.client_identity import get_client_ip, hash_user_agent, sanitize_client_id
from app.services.event_logger import log_event
from app.services.rate_limiter import get_rate_limiter, rate_limit_headers

router = APIRouter(prefix="/demo", tags=["demo"])


def _client_context(request: Request, settings: Settings) -> tuple[str, str | None, str | None]:
    ip = get_client_ip(request, settings)
    client_id = sanitize_client_id(ip)
    ua = request.headers.get("user-agent")
    return client_id, ua, hash_user_agent(ua)


@router.post("/protected", response_model=DemoResponse)
async def protected_demo(
    request: Request,
    response: Response,
    body: DemoRequestBody,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Protected demo endpoint.

    Pipeline: identity → rate limit → bot detection → optional CAPTCHA → log.
    """
    client_id, ua, ua_hash = _client_context(request, settings)
    limiter = get_rate_limiter()
    rl = limiter.check(client_id)
    headers = rate_limit_headers(rl)

    if not rl.allowed:
        event = log_event(
            db,
            RequestEventCreate(
                endpoint="demo.protected",
                http_method="POST",
                outcome="rate_limited",
                risk_score=0,
                classification="suspicious",
                detection_reasons=[
                    DetectionReason(
                        rule="rate_limit",
                        score=0,
                        explanation="Request exceeded configured rate limit.",
                    )
                ],
                rate_limited=True,
                captcha_status="not_required",
                client_id=client_id,
                user_agent_hash=ua_hash,
                status_code=429,
                path=str(request.url.path),
            ),
        )
        payload = DemoResponse(
            status="rate_limited",
            message="Rate limit exceeded. Try again later.",
            risk_score=0,
            classification="suspicious",
            detection_reasons=[{"rule": "rate_limit", "score": 0, "explanation": "Rate limit exceeded."}],
            rate_limited=True,
            event_id=event.id,
        )
        return JSONResponse(
            status_code=429,
            content=payload.model_dump(),
            headers=headers,
        )

    detector = get_bot_detector()
    detection = detector.analyze(
        client_id=client_id,
        endpoint="demo.protected",
        user_agent=ua,
        record=True,
    )

    captcha_status = "not_required"
    captcha_required = detection.captcha_recommended

    if captcha_required:
        captcha = get_captcha_service()
        result = await captcha.verify(body.captcha_token, remote_ip=get_client_ip(request, settings))
        if result.success:
            captcha_status = "passed"
        elif not body.captcha_token:
            captcha_status = "missing"
            event = log_event(
                db,
                RequestEventCreate(
                    endpoint="demo.protected",
                    http_method="POST",
                    outcome="captcha_required",
                    risk_score=detection.risk_score,
                    classification=detection.classification,
                    detection_reasons=[DetectionReason(**r) for r in detection.reasons],
                    rate_limited=False,
                    captcha_status=captcha_status,
                    client_id=client_id,
                    user_agent_hash=ua_hash,
                    status_code=403,
                    path=str(request.url.path),
                ),
            )
            payload = DemoResponse(
                status="captcha_required",
                message="CAPTCHA verification required due to elevated risk score.",
                risk_score=detection.risk_score,
                classification=detection.classification,
                detection_reasons=detection.reasons,
                captcha_required=True,
                captcha_status=captcha_status,
                event_id=event.id,
            )
            return JSONResponse(status_code=403, content=payload.model_dump(), headers=headers)
        else:
            captcha_status = "failed" if "service-failure" not in "".join(result.error_codes) else "error"
            if "verification-service-failure" in result.error_codes:
                captcha_status = "error"
            event = log_event(
                db,
                RequestEventCreate(
                    endpoint="demo.protected",
                    http_method="POST",
                    outcome="captcha_failed",
                    risk_score=detection.risk_score,
                    classification=detection.classification,
                    detection_reasons=[DetectionReason(**r) for r in detection.reasons],
                    rate_limited=False,
                    captcha_status=captcha_status,
                    client_id=client_id,
                    user_agent_hash=ua_hash,
                    status_code=403,
                    path=str(request.url.path),
                ),
            )
            payload = DemoResponse(
                status="captcha_failed",
                message=result.message,
                risk_score=detection.risk_score,
                classification=detection.classification,
                detection_reasons=detection.reasons,
                captcha_required=True,
                captcha_status=captcha_status,
                event_id=event.id,
            )
            return JSONResponse(status_code=403, content=payload.model_dump(), headers=headers)

    # High risk without CAPTCHA configured → still allow but flag (demo safe default)
    outcome = "allowed"
    status_code = 200
    message = f"Request accepted. Echo: {body.message}"

    if detection.classification == "high_risk" and not settings.captcha_enabled:
        # Do not auto-ban; record as allowed-with-suspicion for the demo
        message = (
            "Request accepted with high risk score. CAPTCHA is disabled, so no "
            "challenge was required. Enable CAPTCHA to require verification."
        )

    event = log_event(
        db,
        RequestEventCreate(
            endpoint="demo.protected",
            http_method="POST",
            outcome=outcome,
            risk_score=detection.risk_score,
            classification=detection.classification,
            detection_reasons=[DetectionReason(**r) for r in detection.reasons],
            rate_limited=False,
            captcha_status=captcha_status,
            client_id=client_id,
            user_agent_hash=ua_hash,
            status_code=status_code,
            path=str(request.url.path),
        ),
    )

    for k, v in headers.items():
        response.headers[k] = v

    return DemoResponse(
        status=outcome,
        message=message,
        risk_score=detection.risk_score,
        classification=detection.classification,
        detection_reasons=detection.reasons,
        captcha_required=False,
        captcha_status=captcha_status,
        event_id=event.id,
    )


@router.post("/captcha/verify", response_model=CaptchaVerifyResponse)
async def verify_captcha(
    body: CaptchaVerifyRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> CaptchaVerifyResponse:
    """Server-side CAPTCHA token verification (Turnstile or mock)."""
    captcha = get_captcha_service()
    if not captcha.enabled:
        return CaptchaVerifyResponse(
            success=False,
            provider=settings.captcha_provider,
            error_codes=["captcha-disabled"],
            message="CAPTCHA is disabled in configuration.",
        )
    result = await captcha.verify(body.token, remote_ip=get_client_ip(request, settings))
    return CaptchaVerifyResponse(
        success=result.success,
        provider=result.provider,
        error_codes=result.error_codes,
        message=result.message,
    )
