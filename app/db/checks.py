"""Database health and readiness checks."""

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine


def database_is_ready() -> bool:
    """Return whether a simple PostgreSQL query succeeds."""

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True
    except SQLAlchemyError:
        return False
