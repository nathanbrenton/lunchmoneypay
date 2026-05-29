# Software Requirements Specification

# LunchMoneyPay

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification defines the initial requirements for LunchMoneyPay, a mock third-party payment processor designed to integrate with Homesteady and its ChoreTracker module.

LunchMoneyPay will simulate payment-processing behavior using a fake internal currency called LunchMoney. The system will allow Homesteady to create fake payment intents, confirm fake payments, track wallet balances, write immutable ledger entries, and receive webhook events.

The purpose of this system is educational and architectural. LunchMoneyPay is intended to teach payment-processing concepts without handling real money or payment card data.

### 1.2 Scope

LunchMoneyPay will be a local-first web application and API service.

The MVP will include:

API-based interaction with Homesteady

Fake LunchMoney wallet balances

Ledger-based accounting

Payment intent lifecycle

Fake checkout and approval flow

Webhook event delivery

API key authentication

Idempotency support

Audit logging

Security documentation

Automated tests

LunchMoneyPay will not process real payments, store real card data, connect to card networks, move money between banks, or support real-money withdrawals.

### 1.3 Intended Audience

This document is intended for:

Developer

Software architect

Future maintainers

Security reviewers

Portfolio reviewers

Homesteady project stakeholders

### 1.4 Definitions

Homesteady: Parent household-management platform.

ChoreTracker: Homesteady module used to track chores, self-care, grooming, recurring responsibilities, approvals, and rewards.

LunchMoneyPay: Mock third-party payment processor.

LunchMoney: Fake internal currency used for rewards and redemptions.

Wallet: Account balance container for a user or household member.

Ledger Entry: Immutable accounting record representing a credit, debit, reversal, refund, or adjustment.

Payment Intent: A request to move or credit LunchMoney that follows a lifecycle from creation to confirmation or cancellation.

Webhook: Server-to-server notification sent from LunchMoneyPay to Homesteady.

API Key: Secret credential used by Homesteady to authenticate with LunchMoneyPay.

Idempotency Key: Client-provided key used to prevent duplicate transaction creation.

PCI-DSS: Payment Card Industry Data Security Standard. Used here only as a security-design reference unless real payment card data is introduced.

## 2. Product Overview

### 2.1 Product Perspective

LunchMoneyPay will be developed as a separate local application from Homesteady.

Homesteady will interact with LunchMoneyPay as though it were an external third-party processor. This separation is intentional. It allows the project to practice realistic service boundaries, API contracts, authentication, webhooks, and reconciliation.

Initial deployment model:

Homesteady API runs locally.

LunchMoneyPay API runs locally.

Each application should be independently startable, testable, and version-controlled.

### 2.2 Product Functions

LunchMoneyPay shall provide the following major functions:

Create and manage fake processor accounts.

Create and manage wallets.

Create payment intents.

Confirm or cancel payment intents.

Record immutable ledger entries.

Calculate or retrieve wallet balances.

Create fake checkout sessions.

Send webhook events to registered Homesteady endpoints.

Verify and enforce API key authentication.

Support idempotent transaction creation.

Support refunds, reversals, or manual adjustments.

Provide audit logs for sensitive operations.

### 2.3 User Classes

Developer:

Builds, tests, and maintains LunchMoneyPay.

Homesteady Application:

Calls LunchMoneyPay APIs.

Receives webhook events.

Uses LunchMoneyPay as a fake external processor.

Parent/Admin User:

Approves chore rewards.

May trigger LunchMoney credits or redemptions through Homesteady.

Household Member/User:

Earns and redeems LunchMoney through Homesteady.

System Reviewer:

Reviews the project for architecture, security, and portfolio value.

### 2.4 Operating Environment

LunchMoneyPay shall initially run on:

Debian 13

Python 3

FastAPI

PostgreSQL

SQLAlchemy

Alembic

Local browser access

Localhost-first networking

Future deployment may support LAN access, but the initial MVP shall prioritize local development and testing.

### 2.5 Design and Implementation Constraints

LunchMoneyPay shall not store real payment card data.

LunchMoneyPay shall not process real-money transactions.

LunchMoneyPay shall not connect to actual card networks.

LunchMoneyPay shall not represent itself as a real financial service.

LunchMoneyPay shall use a ledger-based accounting model.

Sensitive configuration shall be stored outside version control.

The system shall be designed for eventual airgapped-friendly development practices.

### 2.6 Assumptions and Dependencies

The system assumes Homesteady will call LunchMoneyPay through HTTP APIs.

The system assumes Homesteady can receive webhooks.

The system assumes PostgreSQL is available locally.

The system assumes LunchMoney has no legal cash value.

The system assumes all payment behavior is simulated unless otherwise explicitly redesigned.

## 3. System Features and Requirements

## 3.1 API Authentication

### 3.1.1 Description

LunchMoneyPay shall authenticate API requests from Homesteady using API keys.

### 3.1.2 Functional Requirements

REQ-AUTH-001: The system shall require API key authentication for protected API endpoints.

REQ-AUTH-002: The system shall store API keys hashed at rest.

REQ-AUTH-003: The system shall display the full API key only at creation time.

REQ-AUTH-004: The system shall reject requests with missing, invalid, disabled, or expired API keys.

REQ-AUTH-005: The system shall record authentication failures in security logs.

REQ-AUTH-006: The system shall support separate API keys for development and future production-like environments.

### 3.1.3 Acceptance Criteria

An unauthenticated request to a protected endpoint returns an authorization error.

A request with a valid API key succeeds if the request is otherwise valid.

The database does not store plaintext API keys.

## 3.2 Accounts

### 3.2.1 Description

Accounts represent external client applications or households using LunchMoneyPay.

### 3.2.2 Functional Requirements

REQ-ACCT-001: The system shall support creation of processor accounts.

REQ-ACCT-002: The system shall assign each account a unique identifier.

REQ-ACCT-003: The system shall associate API keys, wallets, webhooks, and ledger entries with an account.

REQ-ACCT-004: The system shall support account status values such as active, disabled, and test.

### 3.2.3 Acceptance Criteria

A new account can be created.

An account can be retrieved by ID.

Disabled accounts cannot initiate new payment activity.

## 3.3 Wallets

### 3.3.1 Description

Wallets store LunchMoney balances for users or household members.

### 3.3.2 Functional Requirements

REQ-WALLET-001: The system shall create wallets for users.

REQ-WALLET-002: The system shall assign each wallet a unique identifier.

REQ-WALLET-003: The system shall associate wallets with an account.

REQ-WALLET-004: The system shall support balance calculation from ledger entries.

REQ-WALLET-005: The system shall prevent wallet balances from becoming negative unless explicitly allowed by configuration.

REQ-WALLET-006: The system shall expose wallet balance through an authenticated API endpoint.

### 3.3.3 Acceptance Criteria

A wallet can be created for a test user.

A wallet balance reflects the sum of confirmed ledger entries.

Pending transactions do not incorrectly appear as finalized balance unless explicitly represented as pending balance.

## 3.4 Ledger

### 3.4.1 Description

The ledger is the source of truth for all LunchMoney movements.

### 3.4.2 Functional Requirements

REQ-LEDGER-001: The system shall record all LunchMoney movements as ledger entries.

REQ-LEDGER-002: Ledger entries shall be immutable after creation.

REQ-LEDGER-003: Corrections shall be represented by reversal or adjustment entries rather than modifying original entries.

REQ-LEDGER-004: Ledger entries shall include amount, currency, direction, reason, status, source type, source ID, account ID, wallet ID, and timestamp.

REQ-LEDGER-005: Ledger entries shall support statuses such as pending, posted, reversed, failed, and canceled.

REQ-LEDGER-006: The system shall allow ledger entries to be queried by account, wallet, date range, source type, and status.

### 3.4.3 Acceptance Criteria

A confirmed chore reward creates a posted credit ledger entry.

A redemption creates a posted debit ledger entry.

A reversal creates a new ledger entry and does not overwrite the original.

## 3.5 Payment Intents

### 3.5.1 Description

Payment intents represent planned LunchMoney transactions.

### 3.5.2 Functional Requirements

REQ-PI-001: The system shall allow Homesteady to create a payment intent.

REQ-PI-002: A payment intent shall include amount, currency, wallet ID, description, metadata, and status.

REQ-PI-003: The system shall support payment intent statuses such as requires_confirmation, processing, succeeded, canceled, and failed.

REQ-PI-004: The system shall allow payment intents to be confirmed.

REQ-PI-005: Confirming a payment intent shall create the appropriate ledger entry.

REQ-PI-006: The system shall prevent the same payment intent from being confirmed more than once.

REQ-PI-007: The system shall allow payment intents to be canceled before confirmation.

REQ-PI-008: The system shall support metadata fields linking the payment intent to Homesteady entities, such as chore ID, user ID, and approval ID.

### 3.5.3 Acceptance Criteria

A valid payment intent can be created.

A created payment intent can be confirmed.

A confirmed payment intent cannot be confirmed a second time.

A canceled payment intent does not create a posted ledger entry.

## 3.6 Checkout Sessions

### 3.6.1 Description

Checkout sessions simulate a hosted third-party payment approval page.

### 3.6.2 Functional Requirements

REQ-CHECKOUT-001: The system shall allow creation of a fake checkout session.

REQ-CHECKOUT-002: The checkout session shall be associated with a payment intent.

REQ-CHECKOUT-003: The checkout session shall expose a URL for fake approval.

REQ-CHECKOUT-004: The fake checkout page shall allow an authorized test user to approve or cancel the session.

REQ-CHECKOUT-005: Checkout approval shall trigger payment intent confirmation.

REQ-CHECKOUT-006: Checkout cancellation shall cancel the payment intent if it has not already succeeded.

### 3.6.3 Acceptance Criteria

Homesteady can request a checkout session.

LunchMoneyPay returns a fake checkout URL.

Approving the checkout session succeeds the payment intent.

Canceling the checkout session cancels the payment intent.

## 3.7 Webhooks

### 3.7.1 Description

LunchMoneyPay shall notify Homesteady of important payment events through webhooks.

### 3.7.2 Functional Requirements

REQ-WH-001: The system shall allow registration of webhook endpoints.

REQ-WH-002: The system shall generate webhook events for payment intent success, payment intent failure, checkout completion, refund creation, reversal creation, and wallet balance changes.

REQ-WH-003: The system shall sign webhook payloads using a shared secret.

REQ-WH-004: The system shall include timestamp and signature headers with webhook requests.

REQ-WH-005: The system shall retry failed webhook deliveries according to a defined retry policy.

REQ-WH-006: The system shall record webhook delivery attempts.

REQ-WH-007: The system shall provide a test webhook function.

### 3.7.3 Acceptance Criteria

A successful payment intent generates a webhook event.

Homesteady can verify the webhook signature.

Failed webhook delivery attempts are logged.

A test webhook can be sent to a registered endpoint.

## 3.8 Idempotency

### 3.8.1 Description

LunchMoneyPay shall prevent accidental duplicate transactions.

### 3.8.2 Functional Requirements

REQ-IDEMP-001: The system shall accept idempotency keys for transaction-creating endpoints.

REQ-IDEMP-002: The system shall return the original response when a duplicate request uses the same idempotency key and same request body.

REQ-IDEMP-003: The system shall reject a reused idempotency key if the request body differs from the original request.

REQ-IDEMP-004: The system shall store idempotency records for a configurable retention period.

### 3.8.3 Acceptance Criteria

Repeating the same payment intent creation request with the same idempotency key does not create a duplicate payment intent.

Reusing the same idempotency key with a different amount returns an error.

## 3.9 Refunds and Reversals

### 3.9.1 Description

LunchMoneyPay shall support corrections through refunds and reversals.

### 3.9.2 Functional Requirements

REQ-REFUND-001: The system shall support refund or reversal creation for eligible transactions.

REQ-REFUND-002: A refund or reversal shall create a new ledger entry.

REQ-REFUND-003: The original ledger entry shall remain unchanged.

REQ-REFUND-004: The system shall prevent refunding or reversing more LunchMoney than the original transaction amount.

REQ-REFUND-005: Refund and reversal events shall generate webhooks.

### 3.9.3 Acceptance Criteria

A posted credit can be reversed.

The reversal reduces the wallet balance.

The original ledger entry remains visible and unchanged.

## 3.10 Audit Logging

### 3.10.1 Description

LunchMoneyPay shall record security-relevant and accounting-relevant activity.

### 3.10.2 Functional Requirements

REQ-AUDIT-001: The system shall log API key creation.

REQ-AUDIT-002: The system shall log authentication failures.

REQ-AUDIT-003: The system shall log payment intent creation and confirmation.

REQ-AUDIT-004: The system shall log ledger entry creation.

REQ-AUDIT-005: The system shall log webhook endpoint changes.

REQ-AUDIT-006: The system shall log refund and reversal creation.

REQ-AUDIT-007: Audit logs shall include timestamp, actor, action, resource type, resource ID, and outcome.

### 3.10.3 Acceptance Criteria

Security-relevant actions produce audit records.

Audit records can be reviewed during development.

## 4. External Interface Requirements

### 4.1 User Interfaces

The MVP may include a minimal browser interface for fake checkout approval.

The fake checkout page shall clearly indicate that it is a test/simulation page.

The system may later include an admin dashboard for viewing accounts, wallets, payment intents, ledger entries, and webhook deliveries.

### 4.2 API Interfaces

LunchMoneyPay shall expose REST-style JSON APIs.

Initial endpoint groups may include:

/v1/accounts

/v1/wallets

/v1/payment_intents

/v1/checkout/sessions

/v1/ledger

/v1/refunds

/v1/webhook_endpoints

/v1/webhook_events

### 4.3 Database Interfaces

The system shall use PostgreSQL.

The system shall use migrations for schema changes.

The application shall connect using a limited-privilege database user.

### 4.4 Network Interfaces

The system shall initially bind to localhost during development.

LAN access may be added later after firewall and authentication controls are reviewed.

## 5. Non-Functional Requirements

## 5.1 Security

REQ-SEC-001: The system shall not store real cardholder data.

REQ-SEC-002: The system shall not log secrets, API keys, webhook secrets, or sensitive tokens.

REQ-SEC-003: The system shall hash stored API keys.

REQ-SEC-004: The system shall use environment variables or local configuration files excluded from git for secrets.

REQ-SEC-005: The system shall validate all API input.

REQ-SEC-006: The system shall use webhook signatures.

REQ-SEC-007: The system shall support least-privilege database access.

REQ-SEC-008: The system shall include automated security checks where practical.

## 5.2 Reliability

REQ-REL-001: The system shall prevent duplicate transaction creation through idempotency keys.

REQ-REL-002: The system shall preserve ledger history.

REQ-REL-003: The system shall handle failed webhook deliveries without losing event records.

REQ-REL-004: The system shall support repeatable local setup.

## 5.3 Maintainability

REQ-MAINT-001: The system shall use a clear project structure.

REQ-MAINT-002: The system shall include automated tests.

REQ-MAINT-003: The system shall document setup and usage.

REQ-MAINT-004: The system shall maintain a clear separation between API routes, models, schemas, services, and database logic.

## 5.4 Performance

REQ-PERF-001: The system shall respond to ordinary local API requests within an acceptable development-time latency.

REQ-PERF-002: The system shall support basic local load testing.

REQ-PERF-003: The system shall avoid unnecessary blocking operations in webhook delivery where practical.

## 5.5 Portability

REQ-PORT-001: The system shall be designed for Debian 13 local development.

REQ-PORT-002: The system shall use reproducible setup instructions.

REQ-PORT-003: The system shall avoid unnecessary external dependencies during core local development.

## 6. Data Requirements

### 6.1 Core Entities

Initial entities:

Account

API Key

Wallet

Payment Intent

Checkout Session

Ledger Entry

Webhook Endpoint

Webhook Event

Webhook Delivery Attempt

Refund

Reversal

Audit Log Entry

### 6.2 Data Retention

Ledger entries should be retained indefinitely during development.

Audit logs should be retained during development.

Webhook delivery records should be retained long enough to troubleshoot integration behavior.

### 6.3 Data Integrity

Ledger entries shall be immutable.

Transaction operations shall be performed atomically where required.

Wallet balance calculations shall be traceable to ledger entries.

Duplicate transaction creation shall be prevented through idempotency controls.

## 7. Security and Compliance Notes

LunchMoneyPay is not intended to process real cardholder data.

LunchMoneyPay should be designed in a PCI-DSS-inspired manner but should not claim PCI-DSS compliance unless a formal compliance process is performed.

If real payment processing is added later, the preferred approach shall be integration with a validated third-party provider using hosted checkout or embedded provider-controlled payment elements.

The system should avoid bringing cardholder data into Homesteady or LunchMoneyPay.

## 8. MVP Boundaries

### 8.1 Included in MVP

FastAPI app skeleton

PostgreSQL connection

Database models and migrations

Wallet creation

Payment intent creation

Payment intent confirmation

Ledger entry creation

Webhook registration

Webhook event generation

Webhook signature design

Basic tests

README

SRS

### 8.2 Excluded from MVP

Real credit card processing

Real money movement

Bank integrations

Real user identity verification

Tax handling

Payroll handling

Mobile app

Production deployment

Formal PCI-DSS audit

## 9. Future Enhancements

Admin dashboard

Better fake checkout UI

Webhook retry scheduler

Event replay

Reconciliation reports

Balance snapshots

Household allowance budgeting

Scheduled allowance payments

Parent approval workflows

Role-based access control

LAN deployment

Containerized development environment

Offline package bundle

Integration with real third-party provider for funding fake LunchMoney balances

## 10. Open Questions

Should LunchMoney be represented as integer cents to avoid floating-point issues?

Should one LunchMoney equal one fake dollar, or should the unit be abstract?

Should Homesteady own user identity while LunchMoneyPay only stores external references?

Should LunchMoneyPay maintain its own account users, or only external customer references?

Should the fake checkout page be part of LunchMoneyPay MVP or added after API-only flows work?

Should webhook dispatch be synchronous at first, then moved to a background worker later?

Should this project use separate PostgreSQL databases or one database with separate schemas during early development?

## 11. Initial Acceptance Test Goals

A developer can initialize the project.

A developer can run the API locally.

A developer can create a wallet.

A developer can create a payment intent.

A developer can confirm a payment intent.

A confirmed payment intent creates a ledger entry.

A wallet balance reflects the ledger entry.

A webhook event is generated.

Duplicate idempotent requests do not create duplicate transactions.

No real cardholder data exists anywhere in the system.

