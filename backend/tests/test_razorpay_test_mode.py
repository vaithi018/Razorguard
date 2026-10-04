import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import requests
import razorpay.errors

from app.main import app
from app.integrations.razorpay.client import razorpay_client
from app.core.config import settings

client = TestClient(app)


def test_payment_retrieval_success():
    """Validates successful retrieval of a payment from Razorpay Test Mode."""
    mock_payload = {
        "id": "pay_test_succ_100",
        "entity": "payment",
        "amount": 750000,  # 7,500.00 INR
        "currency": "INR",
        "status": "captured",
        "order_id": "order_test_99",
        "method": "card",
        "email": "priya.customer@example.com",
        "contact": "+919876543210",
        "card": {
            "last4": "4242",
            "network": "Visa",
            "type": "credit"
        }
    }

    with patch.object(razorpay_client, "is_configured", True):
        with patch.object(razorpay_client, "_client") as mock_sdk:
            mock_sdk.payment.fetch.return_value = mock_payload

            res = client.get("/api/v1/integrations/razorpay/payments/pay_test_succ_100")
            assert res.status_code == 200
            data = res.json()["data"]
            assert data["payment_id"] == "pay_test_succ_100"
            assert data["amount_inr"] == 7500.0
            assert data["currency"] == "INR"
            assert data["status"] == "captured"
            assert data["customer_email"] == "priya.customer@example.com"
            assert data["is_ingested"] is False


def test_payment_retrieval_invalid_id_returns_404():
    """Validates that a non-existent payment ID returns a clean 404 error without secrets."""
    with patch.object(razorpay_client, "is_configured", True):
        with patch.object(razorpay_client, "_client") as mock_sdk:
            mock_sdk.payment.fetch.side_effect = razorpay.errors.BadRequestError(
                "BAD_REQUEST_ERROR: Payment ID not found"
            )

            res = client.get("/api/v1/integrations/razorpay/payments/pay_invalid_99999")
            assert res.status_code == 404
            assert res.json()["success"] is False
            assert "not found" in res.json()["error"].lower()


def test_payment_retrieval_empty_or_blank_id_returns_400():
    """Validates that an empty or whitespace payment ID is rejected with 400 Bad Request."""
    res = client.get("/api/v1/integrations/razorpay/payments/%20%20")
    assert res.status_code == 400
    assert "valid" in res.json()["error"].lower()


def test_payment_retrieval_api_failure_returns_502():
    """Validates that upstream Razorpay server failures return clean 502 Bad Gateway."""
    with patch.object(razorpay_client, "is_configured", True):
        with patch.object(razorpay_client, "_client") as mock_sdk:
            mock_sdk.payment.fetch.side_effect = razorpay.errors.ServerError(
                "Gateway upstream connection error"
            )

            res = client.get("/api/v1/integrations/razorpay/payments/pay_timeout_err")
            assert res.status_code == 502
            assert res.json()["success"] is False
            assert "upstream errors" in res.json()["error"]


def test_payment_retrieval_timeout_returns_504():
    """Validates that a timeout communicating with Razorpay returns 504 Gateway Timeout."""
    with patch.object(razorpay_client, "is_configured", True):
        with patch.object(razorpay_client, "_client") as mock_sdk:
            mock_sdk.payment.fetch.side_effect = requests.exceptions.Timeout("Connection timed out")

            res = client.get("/api/v1/integrations/razorpay/payments/pay_timedout_test")
            assert res.status_code == 504
            assert res.json()["success"] is False
            assert "timed out" in res.json()["error"].lower()


def test_payment_retrieval_auth_failure_returns_401():
    """Validates that invalid credentials return clean 401 Unauthorized without leaking secrets."""
    with patch.object(razorpay_client, "is_configured", True):
        with patch.object(razorpay_client, "_client") as mock_sdk:
            mock_sdk.payment.fetch.side_effect = razorpay.errors.BadRequestError(
                "Authentication failed: The provided API key is invalid"
            )

            res = client.get("/api/v1/integrations/razorpay/payments/pay_auth_err_test")
            assert res.status_code == 401
            assert res.json()["success"] is False
            assert "authentication failed" in res.json()["error"].lower()


def test_payment_retrieval_malformed_response_returns_502():
    """Validates that a malformed response from Razorpay returns clean 502."""
    with patch.object(razorpay_client, "is_configured", True):
        with patch.object(razorpay_client, "_client") as mock_sdk:
            # Returning an invalid entity (e.g. missing 'id' or not a dict)
            mock_sdk.payment.fetch.return_value = {"error_code": "unknown"}

            res = client.get("/api/v1/integrations/razorpay/payments/pay_malformed_test")
            assert res.status_code == 502
            assert res.json()["success"] is False
            assert "malformed" in res.json()["error"].lower()


def test_missing_credentials_returns_503():
    """Validates that requests fail cleanly with 503 if credentials are not configured."""
    with patch.object(razorpay_client, "is_configured", False):
        with patch.object(razorpay_client, "_client", None):
            res = client.get("/api/v1/integrations/razorpay/payments/pay_any_id")
            assert res.status_code == 503
            assert "credentials are not configured" in res.json()["error"]


def test_prohibited_live_credentials_returns_403():
    """Validates that live credentials (starting with rzp_live_) are strictly forbidden."""
    with patch.object(settings, "RAZORPAY_KEY_ID", "rzp_live_abc123456789"):
        res = client.get("/api/v1/integrations/razorpay/payments/pay_any_live_test")
        assert res.status_code == 403
        assert "production credentials forbidden" in res.json()["error"].lower()


def test_ingest_payment_and_risk_engine_integration():
    """Validates the full flow: payment ingestion -> normalization -> deterministic risk engine -> DB -> audit record."""
    # Ingest a high value payment in paise (120,000 INR = 12000000 paise)
    payload = {
        "payment_id": "pay_test_high_spike_01",
        "amount": 12000000,  # 120,000 INR in paise
        "currency": "INR",
        "status": "captured",
        "email": "corp.buyer@enterprise.in",
        "contact": "+919811223344",
        "method": "card",
        "card": {
            "last4": "8821",
            "network": "MasterCard",
            "type": "corporate"
        }
    }

    res = client.post("/api/v1/integrations/razorpay/payments", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["payment_id"] == "pay_test_high_spike_01"
    assert data["already_processed"] is False
    assert data["normalized_summary"]["amount_inr"] == 120000.0

    # Verify deterministic risk engine evaluated this correctly (120,000 triggers HIGH_AMOUNT tier 2 -> REVIEW)
    assert data["decision"] in ["REVIEW", "BLOCKED"]
    assert data["risk_score"] >= 45

    # Verify audit trail and transaction linking
    txn_id = data["transaction"]["id"]
    detail_res = client.get(f"/api/v1/transactions/{txn_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["data"]["razorpay_payment_id"] == "pay_test_high_spike_01"


def test_ingest_payment_fetches_from_client_when_partial_payload():
    """Validates that ingestion automatically fetches the payment from Razorpay client if details not in body."""
    mock_payload = {
        "id": "pay_test_fetch_auto_01",
        "entity": "payment",
        "amount": 250000,  # 2,500.00 INR
        "currency": "INR",
        "status": "captured",
        "order_id": "order_test_auto_99",
        "method": "upi",
        "email": "auto.fetch@example.com",
        "contact": "+919988776655",
    }

    with patch.object(razorpay_client, "is_configured", True):
        with patch.object(razorpay_client, "_client") as mock_sdk:
            mock_sdk.payment.fetch.return_value = mock_payload

            res = client.post(
                "/api/v1/integrations/razorpay/payments",
                json={"payment_id": "pay_test_fetch_auto_01"}
            )
            assert res.status_code == 200
            data = res.json()["data"]
            assert data["payment_id"] == "pay_test_fetch_auto_01"
            assert data["normalized_summary"]["amount_inr"] == 2500.0
            assert data["decision"] in ["APPROVED", "REVIEW"]


def test_duplicate_payment_idempotency():
    """Validates that submitting the exact same payment_id does not duplicate records or decisions."""
    payload = {
        "payment_id": "pay_test_idempotent_99",
        "amount": 350000,  # 3,500 INR in paise
        "currency": "INR",
        "status": "captured",
        "email": "shopper.idempotent@gmail.com",
        "method": "upi"
    }

    # 1. First submission -> Ingested and processed
    res1 = client.post("/api/v1/integrations/razorpay/payments", json=payload)
    assert res1.status_code == 200
    d1 = res1.json()["data"]
    assert d1["already_processed"] is False
    first_txn_id = d1["transaction"]["id"]
    first_decision = d1["decision"]

    # 2. Second submission with the exact same payment_id -> Must be idempotent!
    res2 = client.post("/api/v1/integrations/razorpay/payments", json=payload)
    assert res2.status_code == 200
    d2 = res2.json()["data"]
    # Verified idempotency
    assert d2["already_processed"] is True
    assert d2["transaction"]["id"] == first_txn_id
    assert d2["decision"] == first_decision
