"""Tests for database configuration and readiness helpers."""

from sqlalchemy import Engine

from app.db.session import SessionLocal, engine


def test_database_engine_uses_configured_postgresql_driver() -> None:
    assert isinstance(engine, Engine)
    assert engine.url.drivername == "postgresql+psycopg"


def test_session_factory_is_bound_to_application_engine() -> None:
    assert SessionLocal.kw["bind"] is engine
