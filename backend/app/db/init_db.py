"""Database schema initialization."""

from app.db.session import Base, engine
from app.models import event  # noqa: F401 — register models


def init_db() -> None:
    """Create all tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
