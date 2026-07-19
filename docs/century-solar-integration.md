# Century Solar integration contract

LunchMoneyPay remains a separate development payment simulator. Century Solar
uses only the HTTP API and never connects to the LunchMoneyPay database.

## Development-only direct checkout

`POST /api/v1/checkout-sessions` is a bounded orchestration endpoint for local
integration testing. It accepts:

- merchant-scoped customer identity and contact fields;
- an external Century Solar order reference;
- amount in minor units;
- three-letter currency;
- `success` or `card_declined` test scenario.

It does not accept card number, CVV/CVC, expiration, track, PIN, authentication,
or raw-provider fields. LunchMoneyPay creates its fixed mock method internally
and returns only the payment-intent identifier, terminal status, error code, and
type/brand/last-four display metadata.

The endpoint requires both `X-API-Key` and `Idempotency-Key`. The fixed demo flow
must be disabled for staging and production. It is not a hosted checkout and is
not suitable for real payment processing.

## Lifecycle mapping

| LunchMoneyPay state | Century Solar state |
| --- | --- |
| `requires_payment_method` | `pending` |
| `processing` | `processing` |
| `succeeded` | `succeeded` |
| `failed` | `failed` |
| `canceled` | `canceled` / failed order payment |

Current payment webhook event names are:

- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `payment_intent.canceled`

Webhook requests use `LunchMoneyPay-Signature` with the existing timestamped
HMAC-SHA256 format. The event data contains bounded payment identity, amount,
currency, state, optional error code, and optional type/brand/last-four summary.

## Local bootstrap

With LunchMoneyPay running on its default nonstandard port:

```bash
python scripts/bootstrap_demo.py;
```

The command creates a merchant credential and one bounded demo checkout. It
prints the plaintext API key once. Keep that key out of source control and place
it only in the local Century Solar `.env` file.

## Assurance boundary

This contract supports integration development and PCI DSS scope minimization
for Century Solar. It is not a PCI certification, legal conclusion, production
processor approval, or authorization to use real cardholder data.
