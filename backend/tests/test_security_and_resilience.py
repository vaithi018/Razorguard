import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.limiter import limiter

client = TestClient(app)


def test_cors_allowed_and_forbidden_origins():
    # 1. Allowed origin returns Access-Control-Allow-Origin
    res_allowed = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert res_allowed.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert res_allowed.headers.get("access-control-allow-credentials") == "true"
    # Never allow '*' with credentials
    assert res_allowed.headers.get("access-control-allow-origin") != "*"

    # 2. Unauthorized origin is not reflected in Access-Control-Allow-Origin
    res_untrusted = client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://malicious-fraud-site.com",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert res_untrusted.headers.get("access-control-allow-origin") != "https://malicious-fraud-site.com"


def test_invalid_transaction_input_validation():
    # Negative amount
    bad_payload_amount = {
        "amount": -500.0,
        "currency": "INR",
        "customer_id": "cust_err_01",
        "customer_email": "valid@email.com",
        "ip_address": "127.0.0.1",
        "payment_method": "card"
    }
    res1 = client.post("/api/v1/transactions", json=bad_payload_amount)
    assert res1.status_code == 422
    data1 = res1.json()
    assert data1["success"] is False
    assert "amount" in data1["error"]
    # Ensure no internal tracebacks or secrets leak
    assert "Traceback" not in data1["error"]

    # Invalid email
    bad_payload_email = {
        "amount": 1000.0,
        "currency": "INR",
        "customer_id": "cust_err_02",
        "customer_email": "invalid_email_format",
        "ip_address": "127.0.0.1",
        "payment_method": "card"
    }
    res2 = client.post("/api/v1/transactions", json=bad_payload_email)
    assert res2.status_code == 422
    data2 = res2.json()
    assert data2["success"] is False
    assert "customer_email" in data2["error"]


def test_missing_openai_api_key_resilience():
    # When OPENAI_API_KEY is empty, deterministic engine MUST still evaluate accurately
    with patch.object(settings, "OPENAI_API_KEY", ""):
        payload = {
            "amount": 1500.0,
            "currency": "INR",
            "customer_id": "cust_resilience_01",
            "customer_email": "clean.shopper@test.com",
            "ip_address": "103.22.45.101",
            "payment_method": "upi"
        }
        res = client.post("/api/v1/transactions", json=payload)
        assert res.status_code == 201
        data = res.json()["data"]
        # Deterministic outcome is preserved
        assert data["decision"] == "APPROVED"
        assert data["risk_score"] == 0
        assert data["ai_enrichment"]["status"] == "DETERMINISTIC_BASELINE"
        assert len(data["ai_enrichment"]["investigation_steps"]) > 0


def test_llm_failure_does_not_change_decision():
    # Simulate OpenAI throwing an API Connection Error or Timeout
    with patch("app.integrations.openai.client.OpenAI") as mock_openai_cls:
        mock_instance = mock_openai_cls.return_value
        mock_instance.chat.completions.create.side_effect = Exception("Connection timeout to OpenAI API")

        # Set a dummy key to trigger the API path
        with patch.object(settings, "OPENAI_API_KEY", "sk-mock-key"):
            payload = {
                "amount": 130000.0,
                "currency": "INR",
                "customer_id": "cust_high_fail_01",
                "customer_email": "high.shopper@test.com",
                "ip_address": "103.22.45.102",
                "payment_method": "card"
            }
            res = client.post("/api/v1/transactions", json=payload)
            assert res.status_code == 201
            data = res.json()["data"]
            # Decision MUST remain REVIEW due to deterministic HIGH_AMOUNT tier 2 rule
            assert data["decision"] == "REVIEW"
            assert data["risk_score"] == 45
            # Status falls back cleanly without breaking transaction
            assert data["ai_enrichment"]["status"] == "FALLBACK_ON_ERROR"
            assert "Enforced deterministically by rule engine" in data["ai_enrichment"]["narrative"]


def test_analyst_authentication_protection():
    # Ingest a transaction first
    payload = {
        "amount": 75000.0,
        "currency": "INR",
        "customer_id": "cust_auth_test",
        "customer_email": "auth.test@example.com",
        "ip_address": "103.22.45.103",
        "payment_method": "card"
    }
    create_res = client.post("/api/v1/transactions", json=payload)
    txn_id = create_res.json()["data"]["id"]

    override_payload = {
        "action": "FORCE_APPROVE",
        "reason": "KYC physically verified by senior compliance manager",
        "analyst_id": "analyst_vip"
    }

    # 1. No authentication header -> 401 Unauthorized
    res_no_auth = client.post(
        f"/api/v1/transactions/{txn_id}/review-action",
        json=override_payload
    )
    assert res_no_auth.status_code == 401
    assert "Authentication required" in res_no_auth.json()["error"]

    # 2. Invalid API key -> 403 Forbidden
    res_wrong_key = client.post(
        f"/api/v1/transactions/{txn_id}/review-action",
        json=override_payload,
        headers={"X-API-Key": "completely_invalid_key_value"}
    )
    assert res_wrong_key.status_code == 403
    assert "Invalid credentials" in res_wrong_key.json()["error"]

    # 3. Valid API key -> 200 OK
    res_valid = client.post(
        f"/api/v1/transactions/{txn_id}/review-action",
        json=override_payload,
        headers={"X-API-Key": settings.ANALYST_API_KEY or "rzg_demo_analyst_key_2026"}
    )
    assert res_valid.status_code == 200
    assert res_valid.json()["data"]["status"] == "MANUALLY_APPROVED"


def test_rules_configuration_protection():
    new_config = {
        "thresholds": {"review_min_score": 45, "blocked_min_score": 75},
        "rules": {}
    }
    # 1. Unauthenticated PUT -> 401
    res_no_auth = client.put("/api/v1/rules/config", json=new_config)
    assert res_no_auth.status_code == 401

    # 2. Authenticated PUT -> 200
    res_auth = client.put(
        "/api/v1/rules/config",
        json=new_config,
        headers={"X-API-Key": settings.ANALYST_API_KEY or "rzg_demo_analyst_key_2026"}
    )
    assert res_auth.status_code == 200
    assert res_auth.json()["data"]["thresholds"]["review_min_score"] == 45


def test_rate_limiting_exceeded():
    # Temporarily set a low limit to test 429 handling cleanly
    with patch.object(settings, "RATE_LIMIT_SIMULATE", "2/minute"):
        # Reset limiter for this test
        limiter.reset()
        
        # 1st request -> OK
        r1 = client.post("/api/v1/transactions/simulate?scenario_key=clean")
        assert r1.status_code == 200

        # 2nd request -> OK
        r2 = client.post("/api/v1/transactions/simulate?scenario_key=clean")
        assert r2.status_code == 200

        # 3rd request -> 429 Too Many Requests
        r3 = client.post("/api/v1/transactions/simulate?scenario_key=clean")
        assert r3.status_code == 429
        assert r3.json()["success"] is False
        assert "Rate limit exceeded" in r3.json()["error"]
        
        # Reset limiter afterwards
        limiter.reset()
