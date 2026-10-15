"""BotShield Lab — FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import analytics, demo, events, health, simulation
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.init_db import init_db

setup_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    # Validate CAPTCHA config early (warn in development, fail closed in production misuse)
    try:
        settings.validate_captcha_config()
    except ValueError as exc:
        if settings.is_production:
            raise
        import logging

        logging.getLogger(__name__).warning("CAPTCHA config warning: %s", exc)
    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "Open-source anti-bot testing platform for demonstrating rate limiting, "
        "explainable bot detection, CAPTCHA verification, and request monitoring "
        "in a controlled local environment. Not production-ready without a "
        "security review."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

prefix = settings.api_prefix
app.include_router(health.router, prefix=prefix)
app.include_router(demo.router, prefix=prefix)
app.include_router(events.router, prefix=prefix)
app.include_router(analytics.router, prefix=prefix)
app.include_router(simulation.router, prefix=prefix)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    """Safe error responses — no stack traces or secrets to clients."""
    import logging

    logging.getLogger(__name__).exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "api": prefix,
        "health": f"{prefix}/health",
    }
