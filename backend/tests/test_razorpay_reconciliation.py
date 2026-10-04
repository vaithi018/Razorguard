import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_db
from app.integrations.razorpay.client import razorpay_client

client = TestClient(app)


def setup_module(module):
    init_db()


def test_razorpay_create_order():
    res = client.post("/api/v1/integrations/razorpay/orders", json={"amount": 4999.0, "currency": "INR"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert "order_id" in data
    assert data["amount"] == 4999.0


def test_reconciliation_clean_payment():
    # Ordinary payment of 1,500 INR -> Approved internally, Captured at Razorpay -> Reconciled cleanly
    res = client.post(
        "/api/v1/integrations/razorpay/simulate-test-payment",
        json={
            "amount": 1500.0,
            "currency": "INR",
            "status": "captured",
            "customer_email": "normal_shopper@gmail.com",
            "method": "upi"
        }
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_discrepant"] is False
    assert data["internal_decision"] == "APPROVED"
    assert data["razorpay_status"] == "captured"


def test_reconciliation_discrepancy_captured_but_blocked():
    # Extreme payment of 450,000 INR -> Blocked by risk rules, but Razorpay captured -> Discrepancy!
    res = client.post(
        "/api/v1/integrations/razorpay/simulate-test-payment",
        json={
            "amount": 450000.0,
            "currency": "INR",
            "status": "captured",
            "customer_email": "high_roller@suspicious.io",
            "method": "card"
        }
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_discrepant"] is True
    assert data["internal_decision"] == "BLOCKED"
    assert data["discrepancy_type"] == "CAPTURED_BUT_BLOCKED"
    assert data["discrepancy_details"]["severity"] == "CRITICAL"


def test_reconciliation_list():
    res = client.get("/api/v1/integrations/razorpay/reconciliation")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] >= 2
    assert len(data["items"]) >= 2
