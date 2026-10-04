import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_db

client = TestClient(app)


def setup_module(module):
    init_db()


def test_create_and_fetch_transaction():
    payload = {
        "amount": 1200.0,
        "currency": "INR",
        "customer_id": "cust_api_test_01",
        "customer_email": "api.test@example.com",
        "ip_address": "122.161.45.10",
        "payment_method": "upi",
    }
    # 1. Ingest transaction
    res = client.post("/api/v1/transactions", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    txn_id = data["data"]["id"]
    assert data["data"]["decision"] == "APPROVED"
    assert data["data"]["risk_score"] == 0
    assert data["data"]["ai_enrichment"] is not None

    # 2. Get transaction detail
    detail_res = client.get(f"/api/v1/transactions/{txn_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()["data"]
    assert detail_data["id"] == txn_id
    assert len(detail_data["audit_logs"]) >= 1

    # 3. List transactions
    list_res = client.get("/api/v1/transactions?page=1&page_size=10")
    assert list_res.status_code == 200
    assert list_res.json()["data"]["total"] >= 1


def test_manual_review_action():
    # Ingest a transaction
    payload = {
        "amount": 95000.0,
        "currency": "INR",
        "customer_id": "cust_review_01",
        "customer_email": "review.user@example.com",
        "ip_address": "122.161.45.22",
        "payment_method": "card",
    }
    res = client.post("/api/v1/transactions", json=payload)
    txn_id = res.json()["data"]["id"]

    # Analyst performs manual review: FORCE_APPROVE
    override_payload = {
        "action": "FORCE_APPROVE",
        "reason": "Verified corporate KYC and confirmed customer authorization",
        "analyst_id": "lead_analyst_raj",
    }
    review_res = client.post(
        f"/api/v1/transactions/{txn_id}/review-action",
        json=override_payload,
        headers={"X-API-Key": "rzg_demo_analyst_key_2026"}
    )
    assert review_res.status_code == 200
    updated_data = review_res.json()["data"]
    assert updated_data["decision"] == "APPROVED"
    assert updated_data["status"] == "MANUALLY_APPROVED"

    # Verify audit trail contains the analyst override
    actions = [a["action"] for a in updated_data["audit_logs"]]
    assert "FORCE_APPROVE" in actions


def test_analytics_metrics_endpoint():
    res = client.get("/api/v1/analytics/metrics")
    assert res.status_code == 200
    metrics = res.json()["data"]
    assert metrics["total_transactions"] >= 1
    assert "risk_distribution" in metrics


def test_simulation_endpoint():
    res = client.post("/api/v1/transactions/simulate?scenario_key=high_amount")
    assert res.status_code == 200
    sim_data = res.json()["data"]
    assert sim_data["decision"] in ["REVIEW", "BLOCKED"]
    assert sim_data["risk_score"] > 0
