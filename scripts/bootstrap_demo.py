#!/usr/bin/env python3
"""Create a Century Solar-oriented LunchMoneyPay demo merchant and checkout."""

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

    request = Request(url, data=body, headers=headers, method=method)

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
    """Create a merchant credential and bounded demo checkout."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:18531")
    parser.add_argument("--merchant-name", default=None)
    parser.add_argument(
        "--scenario",
        choices=("success", "card_declined"),
        default="success",
    )
    parser.add_argument("--amount-minor", type=int, default=125000)
    args = parser.parse_args()

    if args.amount_minor <= 0:
        parser.error("--amount-minor must be positive.")

    base_url = args.base_url.rstrip("/")
    suffix = uuid.uuid4().hex[:10]
    merchant_name = args.merchant_name or f"Century Solar Demo {suffix}"

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

    checkout = request_json(
        "POST",
        f"{base_url}/api/v1/checkout-sessions",
        api_key=api_key,
        idempotency_key=f"century-bootstrap-payment-{suffix}",
        payload={
            "customer_external_reference": f"century-customer-{suffix}",
            "customer_display_name": "Century Solar Demo Customer",
            "customer_email": f"century-demo-{suffix}@example.com",
            "external_reference": f"century-order-{suffix}",
            "amount_minor": args.amount_minor,
            "currency": "USD",
            "test_scenario": args.scenario,
        },
    )

    output = {
        "merchant_id": merchant_id,
        "api_key": api_key,
        "checkout_session_id": checkout["checkout_session_id"],
        "payment_intent_id": checkout["payment_intent_id"],
        "payment_status": checkout["status"],
        "payment_method": checkout["payment_method"],
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
