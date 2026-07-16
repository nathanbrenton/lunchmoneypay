# ChoreTracker integration guide

This guide describes the intended LunchMoneyPay MVP integration contract.
LunchMoneyPay remains a local mock processor; ChoreTracker is the learning and
application project.

## Recommended startup order

1. Start PostgreSQL.
2. Run `alembic upgrade head`.
3. Start LunchMoneyPay on `127.0.0.1:8000`.
4. Confirm `/api/v1/ready` returns HTTP `200`.
5. Start the ChoreTracker webhook receiver.
6. Register the ChoreTracker webhook URL in LunchMoneyPay.

## Initial merchant setup

Merchant creation and credential issuance are administrative bootstrap actions.
The plaintext API key is returned only once.

1. `POST /api/v1/merchants`
2. `POST /api/v1/merchants/{merchant_id}/credentials`
3. Store the returned API key in ChoreTracker's local environment configuration.
4. Verify it with `GET /api/v1/auth/whoami` using `X-API-Key`.

## Typical payment workflow

1. Create or retrieve the ChoreTracker customer.
2. Create a mock payment method for that customer.
3. Create a payment intent with an `Idempotency-Key`.
4. Attach the payment method.
5. Confirm the payment intent.
6. Treat the synchronous response as the immediate processor result.
7. Reconcile the same lifecycle through the signed webhook event.

The mock card scenario belongs to the payment method:

- `success` produces `payment_intent.succeeded`
- `card_declined` produces `payment_intent.payment_failed`

## Refund workflow

Create refunds with `POST /api/v1/refunds` and an `Idempotency-Key`.
LunchMoneyPay supports partial refunds until the original payment amount has
been fully refunded. Successful refunds produce `refund.succeeded` events.

## Idempotency rules

ChoreTracker should generate a unique key for every logical create operation
and persist that key with its own transaction record.

Retry the same request with the same key after timeouts or uncertain responses.
Do not reuse a key for different request content or a different operation.

Suggested key examples:

    choretracker-payment-<local-transaction-uuid>
    choretracker-refund-<local-refund-uuid>

## Webhook registration

Register ChoreTracker's receiver with:

    POST /api/v1/webhook-endpoints

Example body:

    {
      "url": "http://host.docker.internal:8100/webhooks/lunchmoneypay",
      "signing_secret": "replace-with-at-least-32-random-characters"
    }

Use a URL reachable from the LunchMoneyPay process. Container-to-host routing
may differ between macOS and Debian.

## Signature verification

Verify the signature against the exact raw request body before parsing JSON.
Reject stale timestamps according to ChoreTracker's chosen tolerance.

Python example:

    import hashlib
    import hmac
    import time


    def verify_signature(
        secret: str,
        header: str,
        body: bytes,
        tolerance_seconds: int = 300,
    ) -> bool:
        parts = dict(item.split("=", 1) for item in header.split(","))
        timestamp = int(parts["t"])
        supplied = parts["v1"]

        if abs(int(time.time()) - timestamp) > tolerance_seconds:
            return False

        signed = str(timestamp).encode() + b"." + body
        expected = hmac.new(
            secret.encode(),
            signed,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, supplied)

## Event processing

Webhook processing should be idempotent. Persist the LunchMoneyPay event ID and
ignore an event that has already been processed successfully.

Recommended sequence:

1. Read the raw body.
2. Verify the signature and timestamp.
3. Parse the JSON payload.
4. Check whether the event ID has already been processed.
5. Apply the state change in a database transaction.
6. Mark the event as processed.
7. Return a `2xx` response.

## Failure and retry behavior

LunchMoneyPay records failed delivery attempts and provides a manual retry API:

    POST /api/v1/webhook-deliveries/{webhook_delivery_id}/retry

Automated schedules, exponential backoff, dead-letter queues, and worker queues
are intentionally outside this MVP. Those concepts can be explored gradually
inside ChoreTracker.

## Useful reconciliation endpoints

- `GET /api/v1/payment-intents/{id}`
- `GET /api/v1/payment-events?payment_intent_id={id}`
- `GET /api/v1/refunds?payment_intent_id={id}`
- `GET /api/v1/webhook-deliveries?payment_event_id={id}`

ChoreTracker should use these endpoints to resolve uncertain local state during
development and testing.
