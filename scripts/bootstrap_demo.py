#!/usr/bin/env python3
"""Create a minimal LunchMoneyPay demo account and payment workflow."""

import argparse
import json
import secrets
import sys
import uuid
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request_json(
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    api_key: str | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any] | list[dict[str, Any]]:
    """Send one JSON request and return its decoded response."""

    body = None
    headers = {"Accept": "application/json"}

    if payload is not None:
        body = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"

    if api_key is not None:
        headers["X-API-Key"] = api_key

    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key

    request = Request(
        url,
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with urlopen(request, timeout=10) as response:
            response_body = response.read()
    except HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(
            f"{method} {url} returned HTTP {exc.code}: {detail}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(
            f"Unable to reach LunchMoneyPay at {url}: {exc.reason}"
        ) from exc

    return json.loads(response_body)


def main() -> int:
    """Create and print a demo merchant payment workflow."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
    )
    parser.add_argument(
        "--merchant-name",
        default=None,
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    suffix = uuid.uuid4().hex[:10]
    merchant_name = args.merchant_name or f"ChoreTracker Demo {suffix}"

    merchant = request_json(
        "POST",
        f"{base_url}/api/v1/merchants",
        payload={"name": merchant_name},
    )
    merchant_id = merchant["id"]

    credential = request_json(
        "POST",
        f"{base_url}/api/v1/merchants/{merchant_id}/credentials",
    )
    api_key = credential["api_key"]

    customer = request_json(
        "POST",
        f"{base_url}/api/v1/customers",
        api_key=api_key,
        payload={
            "external_reference": f"choretracker-user-{suffix}",
            "display_name": "ChoreTracker Demo User",
            "email": f"demo-{suffix}@example.test",
        },
    )

    payment_method = request_json(
        "POST",
        f"{base_url}/api/v1/payment-methods",
        api_key=api_key,
        payload={
            "customer_id": customer["id"],
            "card_brand": "visa",
            "card_last4": "4242",
            "card_exp_month": 12,
            "card_exp_year": 2030,
            "test_scenario": "success",
        },
    )

    payment_intent = request_json(
        "POST",
        f"{base_url}/api/v1/payment-intents",
        api_key=api_key,
        idempotency_key=f"demo-payment-{suffix}",
        payload={
            "customer_id": customer["id"],
            "external_reference": f"choretracker-payment-{suffix}",
            "amount_minor": 2500,
            "currency": "USD",
        },
    )

    payment_intent = request_json(
        "POST",
        (
            f"{base_url}/api/v1/payment-intents/"
            f"{payment_intent['id']}/attach-payment-method"
        ),
        api_key=api_key,
        payload={"payment_method_id": payment_method["id"]},
    )

    payment_intent = request_json(
        "POST",
        f"{base_url}/api/v1/payment-intents/{payment_intent['id']}/confirm",
        api_key=api_key,
    )

    output = {
        "merchant_id": merchant_id,
        "api_key": api_key,
        "customer_id": customer["id"],
        "payment_method_id": payment_method["id"],
        "payment_intent_id": payment_intent["id"],
        "payment_status": payment_intent["status"],
        "suggested_webhook_secret": secrets.token_urlsafe(32),
    }

    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
