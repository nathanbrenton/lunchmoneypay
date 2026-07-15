"""Tests for the merchant database model."""

from app.models.merchant import Merchant


def test_merchant_uses_expected_table_name() -> None:
    assert Merchant.__tablename__ == "merchants"


def test_merchant_accepts_expected_attributes() -> None:
    merchant = Merchant(
        name="Homesteady",
        status="active",
    )

    assert merchant.name == "Homesteady"
    assert merchant.status == "active"


def test_merchant_table_contains_expected_columns() -> None:
    assert set(Merchant.__table__.columns.keys()) == {
        "id",
        "name",
        "status",
        "created_at",
        "updated_at",
    }


def test_merchant_name_is_unique() -> None:
    assert Merchant.__table__.columns["name"].unique is True


def test_merchant_columns_define_expected_defaults() -> None:
    columns = Merchant.__table__.columns

    assert columns["id"].default is not None
    assert columns["status"].default is not None
    assert columns["created_at"].server_default is not None
    assert columns["updated_at"].server_default is not None
