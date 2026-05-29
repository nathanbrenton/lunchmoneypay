# LunchMoneyPay

LunchMoneyPay is a local-first mock payment processor designed for integration with Homesteady and its ChoreTracker module.

The purpose of this project is to simulate the architecture of a third-party payment processor without handling real money, real bank accounts, or real payment card data. LunchMoneyPay will provide a fake internal currency called LunchMoney, allowing Homesteady users to earn, approve, transfer, redeem, reverse, and audit chore-based rewards.

## Project Purpose

LunchMoneyPay is intended to teach and demonstrate payment-processing concepts safely:

API-based integration between applications

Payment intent lifecycle

Fake checkout and approval flows

Webhook-based event delivery

Ledger-based accounting

Idempotency handling

API key authentication

Audit logging

Refunds and reversals

PCI-DSS-inspired security practices without storing cardholder data

## Important Security Boundary

LunchMoneyPay does not process real payment cards.

LunchMoneyPay does not store, transmit, or process:

Credit card numbers

CVV codes

Expiration dates

Magnetic stripe data

Chip data

Bank account credentials

Real-money withdrawal information

LunchMoney is a fake internal currency for educational and application-design purposes only.

PCI-DSS principles may be used as a security design reference, but LunchMoneyPay is not intended to become a real payment card processor.

## Relationship to Homesteady

Homesteady is the parent platform.

ChoreTracker is a Homesteady module that tracks chores, self-care, grooming, recurring household tasks, approvals, and rewards.

LunchMoneyPay will act as a simulated third-party payment processor that ChoreTracker can call when users earn or redeem LunchMoney.

Example flow:

1. A user completes a chore in ChoreTracker.
2. A parent/admin approves the chore.
3. Homesteady sends a request to LunchMoneyPay.
4. LunchMoneyPay creates a payment intent or ledger entry.
5. LunchMoneyPay confirms the fake transaction.
6. LunchMoneyPay sends a webhook back to Homesteady.
7. Homesteady updates the user’s LunchMoney balance and reward history.

## Planned MVP Features

The first version should include:

FastAPI backend

PostgreSQL database

SQLAlchemy models

Alembic migrations

Local development environment

API key authentication

Payment intent creation

Payment intent confirmation

Ledger entries

Wallet balances

Webhook endpoint registration

Webhook event delivery

Webhook signature verification

Basic fake checkout approval page

Automated tests

Security tooling

## Planned API Resources

Initial resources may include:

Accounts

Users

Wallets

Payment intents

Checkout sessions

Ledger entries

Webhook endpoints

Webhook events

Refunds

Reversals

API keys

## Local Development Goals

LunchMoneyPay should run locally on Debian 13.

Initial local ports:

Homesteady: http://127.0.0.1:8000

LunchMoneyPay: http://127.0.0.1:9000

PostgreSQL: local database service

The app should eventually support LAN access for local household use, but the initial development target is localhost-only.

## Security Goals

LunchMoneyPay should demonstrate responsible payment-style design:

No real cardholder data

No secrets committed to git

Separate application database user

Hashed API keys

Webhook signatures

Idempotency keys

Immutable ledger entries

Audit logs for sensitive events

Input validation

Structured logging

Rate limiting

Least-privilege access

Clear documentation of security boundaries

## Initial Project Structure

Planned structure:

lunchmoneypay/
README.md
docs/
srs/
srs.md
app/
main.py
api/
core/
models/
schemas/
services/
db/
tests/
migrations/
scripts/

## Current Status

Project initialized.

Software Requirements Specification started at:

docs/srs/srs.md

## License

TBD.

## Disclaimer

LunchMoneyPay is an educational mock payment processor. It is not a real financial service, payment card processor, bank, stored-value provider, money transmitter, or payroll system.

