import urllib.request
import json

def verify_razorpay_live():
    # 1. Health check
    res = urllib.request.urlopen("http://127.0.0.1:8000/api/v1/health")
    health = json.loads(res.read().decode())["data"]
    print(f"Health: {health['status']} | Razorpay configured: {health['razorpay_configured']}")

    # 2. Ingest Razorpay Test Mode payment
    payload = {
        "payment_id": "pay_test_live_check_01",
        "amount": 9500000,  # 95,000 INR in paise
        "currency": "INR",
        "status": "captured",
        "email": "corp.treasury@company.in",
        "contact": "+919988776655",
        "method": "card",
        "card": {
            "last4": "5521",
            "network": "Visa",
            "type": "corporate"
        }
    }

    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/integrations/razorpay/payments",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    post_res = urllib.request.urlopen(req)
    data = json.loads(post_res.read().decode())["data"]
    print(f"Ingested Payment: {data['payment_id']} | Amount: ₹{data['normalized_summary']['amount_inr']} | Decision: {data['decision']} | Score: {data['risk_score']}/100 | Already Processed: {data['already_processed']}")

    # 3. Test Idempotency with exact same payment ID
    req_dup = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/integrations/razorpay/payments",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    dup_res = urllib.request.urlopen(req_dup)
    dup_data = json.loads(dup_res.read().decode())["data"]
    print(f"Idempotency Check: Already Processed = {dup_data['already_processed']} | TXN ID unchanged: {dup_data['transaction']['id'] == data['transaction']['id']}")

    # 4. Check Reconciliation List
    recon_res = urllib.request.urlopen("http://127.0.0.1:8000/api/v1/integrations/razorpay/reconciliation")
    recon_data = json.loads(recon_res.read().decode())["data"]
    print(f"Reconciliation Records count: {recon_data['total']}")

if __name__ == "__main__":
    verify_razorpay_live()
