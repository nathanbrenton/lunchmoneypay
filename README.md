# LunchMoneyPay

LunchMoneyPay is a personal, non-commercial mock payment processor for local
service-to-service integration development. It models realistic payment
workflows without processing real money or accepting real payment-card data.
The primary integration target is now Century Solar.

## MVP capabilities

- Merchant accounts and one-time API-key issuance
- Merchant-scoped customer records
- Reusable mock payment methods
- Successful and controlled-decline payment scenarios
- Payment-intent attachment, confirmation, cancellation, and history
- Development-only bounded checkout-session orchestration
- Full and partial refunds
- Durable payment and refund events
- Signed webhook registration, delivery history, and retry
- Idempotent payment-intent, checkout, and refund creation
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

LunchMoneyPay is a development simulator. Never use real payment-card data,
processor credentials, production financial information, or real customer
payment methods. The direct demo checkout is restricted to development/test and
must be disabled in staging and production.

## Local setup

```bash
cp .env.example .env;
python3.13 -m venv .venv;
source .venv/bin/activate;
python -m pip install --upgrade pip;
python -m pip install -e '.[dev]';
docker compose up -d postgres;
alembic upgrade head;
uvicorn app.main:app --host 127.0.0.1 --port 18531;
```

Useful URLs:

- API documentation: `http://127.0.0.1:18531/docs`
- Process health: `http://127.0.0.1:18531/api/v1/health`
- Database readiness: `http://127.0.0.1:18531/api/v1/ready`

## Century Solar bootstrap

With the API running:

```bash
python scripts/bootstrap_demo.py;
```

The script creates a demo merchant, one-time API credential, and a bounded
checkout session. The API key is printed only because the local Century Solar
integration needs it; keep it outside source control.

Merchant-scoped endpoints require:

```text
X-API-Key: <merchant API key>
```

Idempotent create operations use:

```text
Idempotency-Key: <unique client-generated key>
```

See [docs/century-solar-integration.md](docs/century-solar-integration.md) for
the exact checkout and webhook contract.

## Validation

```bash
ruff check .;
ruff format --check .;
pytest -v;
```

## Current release

Version `0.3.0` adds the Century Solar development checkout contract. Hosted
checkout, real acquiring behavior, asynchronous production queues, production
observability, and formal compliance assessment remain outside this simulator.
