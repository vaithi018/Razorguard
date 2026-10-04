# RazorGuard – AI Payment Risk & Reconciliation Agent

RazorGuard is a production-style fintech risk decisioning and reconciliation system. It ingests payment transactions, evaluates fraud vectors through a **100% deterministic rule engine**, records immutable audit trails, reconciles payment gateway outcomes with internal risk policies, and enriches compliance investigations with asynchronous AI narratives.

---

## 🏛️ Core Architectural Principle

```
Razorpay Test Payment
        ↓
Backend Input Validation
        ↓
Normalize Transaction Data
        ↓
Deterministic Risk Engine (Source of Truth)
        ↓
Risk Score (0 - 100) & Decision (APPROVED / REVIEW / BLOCKED)
        ↓
Database (SQLite / PostgreSQL)
        ↓
Immutable Audit Log
        ↓
Optional AI Compliance Explanation (OpenAI gpt-4o-mini)
```

> [!IMPORTANT]
> **Separation of Concerns:**
> 1. **Razorpay** is the payment gateway data source.
> 2. The **Deterministic Rule Engine** is the sole decision authority.
> 3. **OpenAI** is strictly a read-only compliance enrichment layer.
> 4. The LLM is **strictly forbidden** from approving, reviewing, blocking, refunding, capturing, or moving money.

---

## 🔒 Razorpay Test Mode Credentials

> [!CAUTION]
> **TEST MODE ONLY:** This application exclusively operates in Razorpay Test Mode. Production keys (`rzp_live_...`) are prohibited and rejected by the backend security assertions. Real payments must never be processed.

### How to Obtain Test Mode Keys:
1. Log in to the [Razorpay Dashboard](https://dashboard.razorpay.com/).
2. In the top navigation, ensure the environment toggle is set to **Test Mode**.
3. Navigate to **Settings** → **API Keys**.
4. Click **Generate Test Key**.
5. Copy the `Key Id` (starts with `rzp_test_`) and `Key Secret`.
6. Add them to your backend `.env` file.

---

## ⚙️ Environment Configuration

Copy the template from `.env.example`:

```bash
cp .env.example backend/.env
```

| Variable | Description | Example / Default |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Deployment environment | `development` / `production` |
| `DEBUG` | FastAPI debug mode | `True` |
| `API_V1_PREFIX` | API prefix | `/api/v1` |
| `SECRET_KEY` | Application cryptographic secret | *(Random 64-char string)* |
| `ALLOWED_ORIGINS` | Permitted CORS origins (comma-separated, no `*`) | `http://localhost:3000,http://127.0.0.1:3000` |
| `ANALYST_API_KEY` | Key for protecting analyst overrides & rule updates | `rzg_demo_analyst_key_2026` |
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///./razorguard.db` |
| `RAZORPAY_KEY_ID` | Razorpay Test Mode Key ID (must start with `rzp_test_`) | `rzp_test_xxxxxxxxxx` |
| `RAZORPAY_KEY_SECRET` | Razorpay Test Mode Key Secret (strictly backend, never sent to frontend) | `xxxxxxxxxxxxxxxxxxxx` |
| `RAZORPAY_WEBHOOK_SECRET` | Secret for HMAC-SHA256 signature verification | `test_webhook_secret` |
| `OPENAI_API_KEY` | OpenAI API key for risk explanation enrichment | `sk-proj-...` *(optional)* |
| `OPENAI_MODEL` | Low-cost LLM model | `gpt-4o-mini` |
| `RATE_LIMIT_INGESTION` | Ingestion endpoint rate limit | `60/minute` |

---

## 🚀 Local Installation & Running

### 1. Prerequisites
* Python 3.11+ (Python 3.14 compatible)
* Node.js v18+ & npm

### 2. Backend Setup
```bash
cd backend

# Create virtual environment & activate
python -m venv .venv
.\.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start FastAPI backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
* Backend API: `http://127.0.0.1:8000`
* Swagger Documentation: `http://127.0.0.1:8000/docs`
* Health Check: `http://127.0.0.1:8000/api/v1/health`

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev -- --port 3000
```
* Web Application: `http://localhost:3000`

---

## 🧪 Running Automated Tests

The backend test suite includes 33 comprehensive unit and integration tests covering deterministic scoring, CORS enforcement, authentication, rate limiting, LLM fallback, and mocked Razorpay integration:

```bash
cd backend
.\.venv\Scripts\pytest
```

---

## 📡 Razorpay Integration API Endpoints

### 1. Ingest & Evaluate Razorpay Payment
* **`POST /api/v1/integrations/razorpay/payments`**
* **Description:** Ingests a Razorpay Test Mode payment, normalizes it into internal data types, executes the deterministic rule engine, records the outcome, and creates an audit event.
* **Idempotency:** Repeating the same `payment_id` returns the existing transaction without duplicate scoring.
* **Request Example:**
```json
POST /api/v1/integrations/razorpay/payments
Content-Type: application/json

{
  "payment_id": "pay_test_whale_101",
  "amount": 12500000,
  "currency": "INR",
  "status": "captured",
  "email": "corporate.client@enterprise.com",
  "contact": "+919811223344",
  "method": "card",
  "card": {
    "last4": "8821",
    "network": "Visa",
    "type": "corporate"
  }
}
```
* **Response Example (`200 OK`):**
```json
{
  "success": true,
  "data": {
    "payment_id": "pay_test_whale_101",
    "already_processed": false,
    "decision": "REVIEW",
    "risk_score": 45,
    "normalized_summary": {
      "amount_inr": 125000.0,
      "status": "captured",
      "method": "card",
      "email": "corporate.client@enterprise.com"
    },
    "transaction": {
      "id": "c1f7a0...",
      "transaction_ref": "RZP_pay_test_whale_101",
      "amount": 125000.0,
      "decision": "REVIEW",
      "risk_score": 45,
      "status": "REVIEW"
    }
  }
}
```

### 2. Retrieve Payment by ID
* **`GET /api/v1/integrations/razorpay/payments/{payment_id}`**
* **Description:** Retrieves payment details from Razorpay Test Mode and verifies if it is already ingested into the internal ledger.
* **Response Example (`200 OK`):**
```json
{
  "success": true,
  "data": {
    "payment_id": "pay_test_whale_101",
    "amount_inr": 125000.0,
    "currency": "INR",
    "status": "captured",
    "method": "card",
    "customer_email": "corporate.client@enterprise.com",
    "is_ingested": true,
    "internal_decision": "REVIEW",
    "risk_score": 45
  }
}
```

### 3. Webhook Listener
* **`POST /api/v1/integrations/razorpay/webhook`**
* **Header:** `X-Razorpay-Signature: <hmac-sha256>`
* **Description:** Verifies HMAC-SHA256 signature using `RAZORPAY_WEBHOOK_SECRET` and triggers automated reconciliation.

### 4. Reconciliation Ledger
* **`GET /api/v1/integrations/razorpay/reconciliation`**
* **Description:** Returns reconciliation records flagging anomalies such as `CAPTURED_BUT_BLOCKED` (gateway captured payment despite internal rule engine blocking transaction).

---

## 🛡️ Security Highlights

1. **Secret Isolation:** `RAZORPAY_KEY_SECRET` resides strictly in the backend environment and is never exposed in responses or sent to the frontend.
2. **CORS:** Only explicit origins defined in `ALLOWED_ORIGINS` are permitted. Wildcards with credentials are hard-blocked.
3. **Analyst Auth:** Sensitive operations (`/review-action` and `/rules/config`) require an authenticated `X-API-Key` or Bearer token.
4. **Rate Limiting:** Protects public ingestion endpoints against brute-force card testing and DoS bursts.
5. **Fail-Safe AI Layer:** Strict 3.0s timeout with automatic deterministic template fallback if OpenAI is offline or unconfigured.
6. **Strict Test Mode Enforcement:** RazorGuard operates exclusively in Razorpay Test Mode and never uses production credentials. Keys starting with `rzp_live_` are strictly prohibited and rejected by runtime assertions. Real financial transactions are impossible.
7. **Deterministic Decision Authority:** The deterministic rule engine is the sole decision authority. OpenAI is strictly an optional compliance narrative layer and is never permitted to approve, review, block, refund, capture, or move money.
