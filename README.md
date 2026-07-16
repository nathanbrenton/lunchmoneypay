# LunchMoneyPay

LunchMoneyPay is a personal, non-commercial mock payment processor for local
service-to-service integration development. It models realistic payment
workflows without processing real money or storing real card numbers.

The first integration target is ChoreTracker.

## MVP capabilities

- Merchant accounts and one-time API-key issuance
- Merchant-scoped customer records
- Reusable mock card payment methods
- Successful and controlled-decline payment scenarios
- Payment-intent attachment, confirmation, cancellation, and history
- Full and partial refunds
- Durable payment and refund events
- Signed webhook registration, automatic delivery, delivery history, and retry
- Idempotent payment-intent and refund creation
- Health and database-readiness endpoints

## Technology

- Python 3.13
- FastAPI
- PostgreSQL 17
- SQLAlchemy 2
- Alembic
- Pydantic Settings
- pytest and Ruff

## Safety boundary

LunchMoneyPay is a development simulator. Do not use real payment-card data,
real processor secrets, or production financial information.

## Local setup

Create the environment file:

    cp .env.example .env

Replace `API_KEY_PEPPER` with a long random value. Start PostgreSQL using the
project's normal Docker Compose workflow, then apply migrations:

    alembic upgrade head

Start the API:

    uvicorn app.main:app --host 127.0.0.1 --port 8000

Useful URLs:

- API documentation: `http://127.0.0.1:8000/docs`
- Process health: `http://127.0.0.1:8000/api/v1/health`
- Database readiness: `http://127.0.0.1:8000/api/v1/ready`

## Demo bootstrap

With the API running, create a demo merchant, credential, customer, successful
mock card, and payment intent:

    python scripts/bootstrap_demo.py

The script prints the generated IDs and plaintext merchant API key. The API key
is returned only during credential creation; store it securely for local use.

Use a custom API URL when needed:

    python scripts/bootstrap_demo.py --base-url http://127.0.0.1:8000

## Authentication

Merchant-scoped endpoints require:

    X-API-Key: <merchant API key>

Payment-intent and refund creation optionally accept:

    Idempotency-Key: <unique client-generated key>

Reusing the same key with the same request returns the original resource.
Reusing it with different request content returns HTTP `409`.

## Webhooks

Webhook requests include:

- `LunchMoneyPay-Event-Id`
- `LunchMoneyPay-Signature`

The signature format is:

    t=<unix_timestamp>,v1=<hmac_sha256>

The signed message is:

    <timestamp>.<raw_request_body>

See [docs/choretracker-integration.md](docs/choretracker-integration.md) for the
recommended ChoreTracker workflow and a Python verification example.

## Validation

Run all checks before committing:

    ruff check .
    pytest -v

## Current release

Version `0.2.0` is the integration-ready MVP baseline for ChoreTracker.
Advanced retry scheduling, asynchronous queues, production observability, and
third-party processor behavior are intentionally deferred.
