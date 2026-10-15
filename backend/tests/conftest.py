"""Shared pytest fixtures — isolated SQLite DB and reset services."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Configure test environment before importing the app
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["RATE_LIMIT_ENABLED"] = "true"
os.environ["RATE_LIMIT_REQUESTS"] = "5"
os.environ["RATE_LIMIT_WINDOW_SECONDS"] = "60"
os.environ["RATE_LIMIT_STORAGE"] = "memory"
os.environ["CAPTCHA_ENABLED"] = "true"
os.environ["CAPTCHA_PROVIDER"] = "mock"
os.environ["CAPTCHA_MOCK_ENABLED"] = "true"
os.environ["CAPTCHA_MOCK_VALID_TOKEN"] = "mock-valid-token"
os.environ["DETECTION_FREQUENCY_THRESHOLD"] = "3"
os.environ["DETECTION_REPEAT_ENDPOINT_THRESHOLD"] = "3"
os.environ["DETECTION_SUSPICIOUS_SCORE_THRESHOLD"] = "40"
os.environ["DETECTION_HIGH_RISK_SCORE_THRESHOLD"] = "70"
os.environ["DETECTION_CAPTCHA_TRIGGER_SCORE"] = "40"
os.environ["DETECTION_WINDOW_SECONDS"] = "60"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"
os.environ["SIMULATION_MAX_REQUESTS"] = "20"
os.environ["SIMULATION_MIN_INTERVAL_MS"] = "50"

from app.core.config import Settings, get_settings  # noqa: E402
from app.db.session import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.services.bot_detector import reset_bot_detector  # noqa: E402
from app.services.captcha import reset_captcha_service  # noqa: E402
from app.services.rate_limiter import reset_rate_limiter  # noqa: E402


@pytest.fixture()
def settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session, settings):
    def _override_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_db
    reset_bot_detector(settings)
    reset_rate_limiter(settings)
    reset_captcha_service(settings)

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    reset_bot_detector(settings)
    reset_rate_limiter(settings)
