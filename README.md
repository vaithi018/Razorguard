# RazorGuard

Production-grade payment risk, fraud simulation, and reconciliation control center powered by deterministic decisioning.

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [System Architecture](#-system-architecture)
- [Key Features](#-key-features)
- [Deterministic Rule Engine](#-deterministic-rule-engine)
- [Fraud Simulation](#-fraud-simulation)
- [Razorpay Reconciliation](#-razorpay-reconciliation)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Local Setup & Running](#-local-setup--running)
- [Testing](#-testing)
- [Security & Production Considerations](#-security--production-considerations)
- [Why This Project?](#-why-this-project)
- [Demo](#-demo)
- [Screenshots](#-screenshots)
- [Future Enhancements](#-future-enhancements)
- [Final Summary](#-final-summary)

---

## 🌐 Project Overview

In digital payment workflows, merchants and payment platforms face three critical operational challenges:
1. **Financial Fraud & Chargebacks:** High-velocity card testing attacks, sudden ticket size spikes, and unauthorized credential reuse lead to immediate chargeback liability, gateway fines, and reputational risk.
2. **Unexplainable Black-Box Decisioning:** Non-deterministic systems (such as direct LLM evaluations or opaque scoring algorithms) are prone to hallucinations, inconsistent outputs for identical inputs, and an inability to provide strict legal and regulatory audit trails.
3. **Gateway Settlement Discrepancies:** Payment gateways can capture transactions that internal risk engines flag as high risk or blocked. Without continuous, automated reconciliation, settled funds may leave the business before suspicious activity is reviewed.

### What Problem RazorGuard Solves
RazorGuard is an operational control center that addresses these challenges by:
- **Enforcing 100% Deterministic Decisioning:** Transaction risk is scored through mathematically bounded, reproducible rules. The exact same transaction evaluated against the same configuration will always produce the identical score and decision (`APPROVED`, `REVIEW`, or `BLOCKED`).
- **Simulating Attack Vectors Interactively:** A dedicated fraud simulator enables risk analysts and engineers to test card testing, rapid succession, velocity spikes, and high-ticket scenarios against the rule engine in real time.
- **Automating Gateway Reconciliation:** Synchronizing Razorpay Test Mode gateway events against internal risk decisions to automatically flag settlement discrepancies (such as payments captured by the gateway despite an internal `BLOCKED` or `REVIEW` decision).

---

## 🏛️ System Architecture

RazorGuard separates transactional risk evaluation from gateway reconciliation into two decoupled, deterministic pipelines:

### 1. Transaction Risk & Decision Pipeline

```text
Transaction Input (API / Simulator)
        ↓
Input Validation & Schema Normalization (Pydantic v2)
        ↓
Context Builder (Historical Customer Velocity & Volumes)
        ↓
Deterministic Risk Engine (Evaluates Active Rule Set)
        ↓
Risk Score Calculation (0 - 100 Bounded Scale)
        ↓
Decision Boundary Evaluation (APPROVED / REVIEW / BLOCKED)
        ↓
Transaction Ledger & Immutable Audit Trail (SQLite / PostgreSQL)
        ↓
Asynchronous Compliance Enrichment (Optional AI Narrative)
```

### 2. Razorpay Reconciliation Pipeline

```text
Razorpay Test Mode Gateway (Payment / Webhook Event)
        ↓
Payment Ingestion & Status Normalization
        ↓
Reconciliation Engine (Gateway State vs. Internal Decision)
        ↓
Discrepancy Classifier (CAPTURED_BUT_BLOCKED / CAPTURED_UNDER_REVIEW / CLEAN)
        ↓
Reconciliation Ledger with Recommended Analyst Remediation
```

---

## ✨ Key Features

Only features that exist in the codebase:

- **Deterministic Risk Engine:** Sub-millisecond evaluation across an array of explicitly defined, modular risk rules.
- **Configurable Risk Score Thresholds:** Dynamic calibration of `Review Minimum` and `Blocked Minimum` boundaries on a bounded 0–100 scale.
- **High-Amount Transaction Rules:** Stepped ticket-size evaluation adding calibrated points for Tier 1, Tier 2, and Extreme amount thresholds.
- **Velocity & Rate Anomaly Detection:** Rolling 10-minute transaction count limits to detect automated purchasing scripts.
- **Rapid Succession (Card Testing) Detection:** Micro-window evaluation (e.g. <30 seconds between attempts) to avert BIN attack testing.
- **Daily Cumulative Volume Spike Detection:** 24-hour historical volume aggregation to catch sudden account drainage or abnormal ticket surges.
- **Failed Attempt Burst Rules:** Identification of repeated decline bursts indicating stolen card credential brute-forcing.
- **Blocklist Enforcement:** Zero-tolerance hard blocking for known malicious emails, cards, or identifiers.
- **Unusual Hours Adjustment:** Nighttime processing risk adjustments for sensitive customer segments.
- **Interactive Fraud Attack Simulator:** Built-in attack vector presets (Clean Shopper, High-Risk Attack, Velocity Burst, Cumulative Volume Spike, Rapid Succession Card Testing) plus custom payload generation.
- **Transaction Ledger & Detail Inspector:** Filterable, searchable operations ledger with slide-over drawer showing full rule evaluations, point impacts, and audit records.
- **Risk Score Distribution:** Real-time visual categorization across Low, Medium, and High risk bands.
- **Razorpay Test Mode Integration:** Direct API integration using Razorpay Test Mode credentials (`rzp_test_...`) with Payment ID inspector and webhook listener.
- **Automated Gateway Reconciliation:** Discrepancy detection engine comparing gateway payment status against internal risk decisions.
- **Clear Decision Outcomes:** Unambiguous `APPROVED` (safe), `REVIEW` (analyst intervention required), and `BLOCKED` (immediate rejection) states.
- **Explainable Rule Hits:** Every transaction records exactly which rules triggered, why they triggered, and their exact score contribution.

---

## ⚙️ Deterministic Rule Engine

> [!IMPORTANT]
> **Core Principle:** Critical financial and payment decisions are **never** delegated to an LLM or probabilistic model. 

### Why Determinism Matters in Payment Systems
1. **Mathematical Reproducibility:** `Input + Rule Set = Deterministic Output`. Given identical inputs and parameters, the system outputs the identical risk score and decision every single time.
2. **Auditability & Compliance:** Financial auditors, regulatory bodies, and payment card brands require explainable justifications for declined transactions. RazorGuard logs every rule triggered, the evaluation context, and the point weight applied.
3. **Low Latency:** In-memory rule execution completes in sub-milliseconds without blocking on external network calls.
4. **Separation of Concerns:** Optional AI compliance enrichment operates **strictly read-only** and asynchronously. The LLM is architecturally forbidden from approving, reviewing, blocking, capturing, or moving money.

### Rule Scoring Breakdown

| Rule ID | Vector Checked | Default Threshold | Default Impact |
| :--- | :--- | :--- | :--- |
| `BLOCKLIST` | Malicious email / identifier match | Instant match | **Hard Block (Score 100)** |
| `HIGH_AMOUNT` | Stepped ticket size anomaly | > ₹50,000 / ₹100,000 / ₹300,000 | +25 / +45 / +75 pts |
| `VELOCITY_10M` | Transaction count in 10-minute window | > 3 transactions | +25 pts |
| `RAPID_SUCCESSION` | Seconds between consecutive transactions | < 30 seconds | +35 pts |
| `FAILED_BURST` | Multiple payment failures within window | > 2 failures in 10 min | +30 pts |
| `DAILY_CUMULATIVE_VOLUME` | Total rolling volume in 24 hours | > ₹200,000 | +30 pts |
| `UNUSUAL_HOURS` | Off-peak processing activity | 01:00 AM – 05:00 AM | +15 pts |

---

## 🎯 Fraud Simulation

The integrated **Risk Simulator** provides risk engineering teams with an automated playground to validate rule configurations against realistic attack vectors without impacting real payments:

- **Clean E-Commerce Shopper (`APPROVED`):** Standard consumer purchase (₹2,499) with legitimate profile details, testing the baseline safe path.
- **High-Risk Ticket Attack (`BLOCKED`):** Extreme ticket size (₹350,000) from an unverified customer triggering extreme amount thresholds.
- **Velocity Burst (`REVIEW` / `BLOCKED`):** Rapid succession transactions from the same account simulating automated checkout bots.
- **Daily Cumulative Volume Spike (`REVIEW`):** Rolling 24-hour volume accumulation simulating account takeover or sudden abnormal spending.
- **Card Testing Attack Vector (`REVIEW`):** Rapid repeat attempts within seconds checking for automated card testing patterns.
- **Custom Parameter Simulation:** Form-based builder allowing custom amounts, currencies, customer emails, and payment methods.

---

## 🔄 Razorpay Reconciliation

In production environments, payment gateways and merchant risk engines can fall out of sync. For example, a payment may be captured by the gateway before an asynchronous risk assessment flags the transaction.

RazorGuard's **Reconciliation Engine** bridges this gap:

1. **Safe Test Mode Integration:** Operates exclusively using Razorpay Test Mode API credentials (`rzp_test_...`). Production keys are strictly blocked.
2. **Gateway Payment Inspector:** Fetches live transaction data by Razorpay Payment ID and runs it through the deterministic rule engine.
3. **Discrepancy Identification:**
   - **`CAPTURED_BUT_BLOCKED`:** Gateway captured the payment, but the internal risk engine determined the transaction is `BLOCKED`. Surfaced immediately with recommended action: *"Initiate immediate refund / void authorization"*.
   - **`CAPTURED_UNDER_REVIEW`:** Gateway authorized/captured funds, but internal risk score requires manual analyst sign-off before order fulfillment.
   - **`RECONCILED_CLEAN`:** Gateway state matches internal risk authorization.
4. **Reconciliation Ledger:** Dedicated operational ledger displaying gateway status, internal decision, discrepancy classification, and recommended action.

---

## 💻 Tech Stack

Technologies verified from project configuration and source code:

### Frontend
- **Framework:** [Next.js 16](https://nextjs.org/) (App Router, Turbopack)
- **Library:** [React 19](https://react.dev/)
- **Language:** [TypeScript](https://www.typescriptlang.org/)
- **Styling:** [Tailwind CSS v4](https://tailwindcss.com/)
- **Icons:** [Lucide React](https://lucide.dev/)

### Backend
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+ / Python 3.12 compatible)
- **ASGI Server:** [Uvicorn](https://www.uvicorn.org/)
- **Data Validation & Settings:** [Pydantic v2](https://docs.pydantic.dev/) & [pydantic-settings](https://github.com/pydantic/pydantic-settings)
- **Database & ORM:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (SQLite for zero-config local/serverless execution, PostgreSQL compatible)
- **Migrations:** [Alembic](https://alembic.sqlalchemy.org/)
- **Rate Limiting:** [SlowAPI](https://github.com/laurentS/slowapi)
- **HTTP Client:** [HTTPX](https://www.python-httpx.org/)

### Integrations & Services
- **Payment Gateway:** [Razorpay Python SDK](https://github.com/razorpay/razorpay-python) (`razorpay>=1.4.1`)
- **Compliance Enrichment:** [OpenAI Python SDK](https://github.com/openai/openai-python) (`openai>=1.14.0`, optional asynchronous narrative generator)

### Testing & Infrastructure
- **Test Suite:** [Pytest](https://docs.pytest.org/) (39 automated unit & integration tests)
- **Deployment Platform:** [Vercel](https://vercel.com/) (Multi-service deployment for frontend and backend)

---

## 📁 Project Structure

```text
Razorguard/
├── .env.example                     # Environment template with placeholders
├── .gitignore                       # Protection for credentials, venv, and build artifacts
├── README.md                        # Project documentation
├── vercel.json                      # Vercel multi-service project routing configuration
│
├── backend/                         # FastAPI backend service
│   ├── alembic/                     # Database schema migration scripts
│   ├── alembic.ini                  # Alembic configuration
│   ├── main.py                      # Serverless entrypoint exporting FastAPI app
│   ├── run.py                       # Local Uvicorn server launcher
│   ├── requirements.txt             # Python dependencies
│   ├── pytest.ini                   # Pytest test discovery configuration
│   ├── config/
│   │   └── rules_config.json        # Calibrated risk rule parameters & cutoffs
│   ├── app/
│   │   ├── main.py                  # FastAPI app factory, CORS, exception handlers, lifespan
│   │   ├── api/v1/
│   │   │   ├── router.py            # Aggregated v1 API router
│   │   │   └── endpoints/
│   │   │       ├── health.py        # System health and component status check
│   │   │       ├── transactions.py  # Ingestion, query, detail, and analyst override APIs
│   │   │       ├── analytics.py     # KPI volume metrics and rule trigger leaderboard
│   │   │       ├── rules.py         # Dynamic rule threshold calibration API
│   │   │       └── razorpay_sync.py # Gateway ingestion, inspector, and recon endpoints
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic BaseSettings environment validation
│   │   │   ├── database.py          # SQLAlchemy engine, session factory, Base metadata
│   │   │   ├── security.py          # Analyst authentication and API key validation
│   │   │   └── limiter.py           # SlowAPI client IP rate limiter
│   │   ├── engine/
│   │   │   ├── base.py              # BaseRule abstract class and RuleResult schema
│   │   │   ├── context.py           # EvaluationContext containing transaction & customer history
│   │   │   ├── evaluator.py         # DeterministicRuleEngine evaluator and score aggregator
│   │   │   └── rules/               # Individual rule implementations
│   │   │       ├── blocklist.py
│   │   │       ├── high_amount.py
│   │   │       ├── velocity.py
│   │   │       ├── rapid_succession.py
│   │   │       ├── failed_burst.py
│   │   │       ├── cumulative_volume.py
│   │   │       └── unusual_hours.py
│   │   ├── integrations/
│   │   │   ├── razorpay/client.py   # Isolated Razorpay API communication client
│   │   │   └── openai/              # Asynchronous compliance explanation & fallback
│   │   ├── models/                  # SQLAlchemy ORM models (Transaction, AuditLog, Recon, etc.)
│   │   ├── schemas/                 # Pydantic request/response validation schemas
│   │   └── services/                # Business logic, context builder, and reconciliation service
│   └── tests/                       # 39 automated unit, integration, and security tests
│
└── frontend/                        # Next.js frontend application
    ├── package.json                 # Node dependencies and scripts
    ├── next.config.ts               # Next.js config with development API rewrites
    ├── tsconfig.json                # TypeScript compiler configuration
    └── src/
        ├── app/
        │   ├── layout.tsx           # Root HTML layout and metadata
        │   ├── page.tsx             # Main dashboard container and tab switcher
        │   └── globals.css          # Fintech design system CSS tokens and theme variables
        ├── components/
        │   ├── Navbar.tsx           # Enterprise header with real-time Engine Active indicator
        │   ├── MetricCard.tsx       # KPI summary cards
        │   ├── RiskDistributionChart.tsx # Low / Medium / High distribution bar
        │   ├── RiskScoreGauge.tsx   # SVG risk score gauge
        │   ├── TransactionsTable.tsx # Filterable transaction ledger
        │   ├── TransactionDrawer.tsx # Slide-over rule breakdown & audit inspector
        │   ├── SimulatorTab.tsx     # Interactive attack vector simulator
        │   ├── ReconciliationTab.tsx # Gateway payment inspector and reconciliation ledger
        │   └── RulesConfigTab.tsx   # Decision score threshold calibration controls
        ├── lib/
        │   ├── api.ts               # Typed frontend HTTP client
        │   └── utils.ts             # Currency, date, and badge styling utilities
        └── types/
            └── index.ts             # TypeScript domain interfaces
```

---

## 🚀 Local Setup & Running

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** & **npm**
- **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/vaithi018/Razorguard.git
cd Razorguard
```

### 2. Configure Environment
```bash
# Copy backend environment template
cp .env.example backend/.env
```
Update `backend/.env` with your values. For test execution, defaults are pre-configured.

### 3. Start Backend Service
```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate      # Windows PowerShell
# source .venv/bin/activate    # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start FastAPI server
python run.py
```
- **API URL:** `http://127.0.0.1:8000`
- **Swagger Documentation:** `http://127.0.0.1:8000/docs`
- **Health Endpoint:** `http://127.0.0.1:8000/api/v1/health`

### 4. Start Frontend Application
In a separate terminal:
```bash
cd frontend

# Install Node dependencies
npm install

# Start Next.js development server
npm run dev
```
- **Control Center:** `http://localhost:3000`

---

## 🧪 Testing

The backend includes a comprehensive automated test suite with **39 passing tests** covering deterministic scoring, rule boundaries, security assertions, and gateway reconciliation:

```bash
cd backend
pytest
```

### Scenarios Tested:
1. **Low-Risk Transaction (`APPROVED`):** Normal purchase amounts within baseline thresholds output a score < 40 and decision `APPROVED`.
2. **High-Risk Ticket (`BLOCKED`):** Extreme ticket sizes trigger stepped amount rules, outputting score ≥ 70 and decision `BLOCKED`.
3. **Medium-Risk Velocity Spike (`REVIEW`):** Multiple transactions in a short window cross the review boundary (40–69 pts).
4. **Rapid Succession / Card Testing:** Transactions within seconds from the same entity trigger the `RAPID_SUCCESSION` rule (+35 pts).
5. **Cumulative Daily Volume:** Rolling 24-hour volume accumulation triggers the `DAILY_CUMULATIVE_VOLUME` rule (+30 pts).
6. **Blocklist Enforcement:** Transactions matching blocklisted identifiers trigger an instant score of 100 with hard block.
7. **Razorpay Reconciliation Discrepancy:** Automated reconciliation correctly identifies gateway payments captured despite an internal `BLOCKED` or `REVIEW` decision (`CAPTURED_BUT_BLOCKED`).
8. **Security & Resilience:** CORS header verification, rate limiting enforcement, invalid payload validation, and LLM fallback resilience when API keys are absent.

---

## 🔒 Security & Production Considerations

*(Future production improvements)*

For large-scale, enterprise financial production environments, the following roadmap enhancements are recommended:

- **Enhanced Authentication & Access Control:** Transition from API key headers to OAuth 2.0 / OIDC with multi-factor authentication (MFA) and fine-grained Role-Based Access Control (RBAC) for analysts.
- **Dedicated Secret Management:** Move production credentials from environment variables into a managed vault (AWS Secrets Manager, HashiCorp Vault, or Google Cloud Secret Manager) with automatic rotation.
- **Distributed Rate Limiting:** Back SlowAPI with a distributed Redis cluster to enforce rate limits across horizontally scaled serverless replicas.
- **Managed Persistent Database:** Migrate SQLite storage to a high-availability managed PostgreSQL cluster (such as AWS RDS, Neon, or Supabase) with connection pooling via PgBouncer.
- **Enterprise Observability:** Integrate OpenTelemetry instrumentation with distributed tracing (Datadog, Prometheus, or Grafana) for real-time latency and rule hit metrics.
- **Cryptographic Audit Log Verification:** Implement SHA-256 hash chaining on audit trail entries to guarantee non-repudiation and tamper evidence.
- **Asynchronous Webhook Processing Queue:** Process inbound gateway webhooks through a resilient message broker (RabbitMQ, Apache Kafka, or AWS SQS) with dead-letter queueing and exponential backoff retry.
- **Circuit Breakers:** Implement circuit breakers on external service calls (gateway APIs and compliance LLMs) to prevent cascading timeouts.

---

## 💡 Why This Project?

Financial payment systems cannot afford non-deterministic behavior. When evaluating whether to authorize, hold, or decline a customer's transaction:
- A false positive frustrates legitimate customers and directly damages conversion rates.
- A false negative exposes the business to chargebacks, card brand penalties, and fraud losses.
- A non-deterministic decision (such as relying on generative LLM prompts for approval) cannot be explained to a financial auditor, lacks reproducibility, and introduces critical security vulnerabilities.

**RazorGuard delivers a modern architecture:**
1. **Financial Decisions are Deterministic:** 100% of transaction routing, risk scoring, and rule triggering is handled by an auditable, deterministic rule engine.
2. **AI is Strictly Informational:** Generative AI is relegated strictly to an asynchronous compliance layer that summarizes why rules fired for human review, never touching money movement.
3. **Reconciliation Protects Settlement:** Gateway events are continuously reconciled against internal risk policies, catching discrepancies before settlement funds are cleared.

---

## 🌐 Demo

- **Live Operations Console:** [https://razorguard-puce.vercel.app](https://razorguard-puce.vercel.app)
- **GitHub Repository:** [https://github.com/vaithi018/Razorguard](https://github.com/vaithi018/Razorguard)
- **Demo Video:** `[Demo Video Link Placeholder]`

---

## 📸 Screenshots

<!-- 
Add your screenshots below by placing image files in the repository (e.g. in a /docs/screenshots folder) and updating the links:
-->

### 1. Operations Dashboard
<!-- ![Operations Dashboard](docs/screenshots/dashboard.png) -->
*Real-time volume tracking, risk score distribution, rule trigger leaderboard, and live transaction ledger.*

### 2. Fraud Attack Simulator
<!-- ![Fraud Simulator](docs/screenshots/simulator.png) -->
*Simulate clean transactions, velocity bursts, card testing attacks, and cumulative volume spikes with instant score evaluation.*

### 3. Transaction Detail & Audit Inspector
<!-- ![Transaction Inspector](docs/screenshots/drawer.png) -->
*Slide-over drawer providing granular breakdown of rule evaluations, score impact, and compliance audit trail.*

### 4. Rule Engine Calibration
<!-- ![Rule Engine](docs/screenshots/rule_engine.png) -->
*Interactive threshold calibration for Review Minimum, Blocked Minimum, and ticket-size stepped rule parameters.*

### 5. Razorpay Reconciliation & Gateway Discrepancy Guard
<!-- ![Razorpay Reconciliation](docs/screenshots/reconciliation.png) -->
*Reconciliation ledger comparing Razorpay gateway status against internal risk decisions to surface discrepancies.*

---

## 🔮 Future Enhancements

- **Machine Learning Shadow Scoring:** Run ML risk models in parallel shadow mode to benchmark against deterministic rule baseline without decision authority.
- **Automated Webhook Dispute Resolution:** Automatic webhook-triggered refund dispatch when high-confidence fraud is confirmed post-capture.
- **Multi-Merchant Organization Support:** Tenant isolation allowing distinct rule sets, velocity counters, and risk boundaries per merchant account.
- **Exportable Regulatory Reports:** Automated PDF/CSV export of audit trails formatted for PCI-DSS compliance and financial dispute reviews.

---

## 📝 Final Summary

RazorGuard provides an end-to-end payment risk and reconciliation control center engineered for enterprise fintech operations. By combining deterministic rule evaluation, interactive attack simulation, and automated gateway reconciliation, it offers payment platforms a reliable, explainable, and auditable foundation for payment integrity.
