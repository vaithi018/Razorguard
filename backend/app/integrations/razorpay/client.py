import hmac
import hashlib
import uuid
import logging
from typing import Dict, Any, List, Optional
import requests
import razorpay
import razorpay.errors
from app.core.config import settings

logger = logging.getLogger("razorguard.razorpay")


class RazorpayIntegrationError(Exception):
    """Base exception for Razorpay integration issues."""
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class RazorpayConfigError(RazorpayIntegrationError):
    """Raised when Razorpay credentials are missing or invalid."""
    def __init__(self, message: str = "Razorpay Test Mode credentials are not configured. Please configure RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env."):
        super().__init__(message, status_code=503)


class RazorpayLiveCredentialProhibitedError(RazorpayIntegrationError):
    """Raised when a production/live credential ('rzp_live_') is detected."""
    def __init__(self, message: str = "PRODUCTION CREDENTIALS FORBIDDEN: RazorGuard strictly operates in TEST MODE only. Credentials starting with 'rzp_live_' are prohibited."):
        super().__init__(message, status_code=403)


class RazorpayPaymentNotFoundError(RazorpayIntegrationError):
    """Raised when a payment ID does not exist in Razorpay."""
    def __init__(self, payment_id: str):
        super().__init__(f"Payment ID '{payment_id}' was not found in Razorpay Test Mode.", status_code=404)


class RazorpayInvalidPaymentIdError(RazorpayIntegrationError):
    """Raised when a payment ID is malformed or invalid."""
    def __init__(self, message: str = "A valid Razorpay Test Mode payment ID is required (e.g. 'pay_test_...')."):
        super().__init__(message, status_code=400)


class RazorpayAuthError(RazorpayIntegrationError):
    """Raised when authentication with Razorpay API fails (invalid key or secret)."""
    def __init__(self, message: str = "Authentication failed with Razorpay API. Please verify RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET."):
        super().__init__(message, status_code=401)


class RazorpayTimeoutError(RazorpayIntegrationError):
    """Raised when Razorpay API request times out."""
    def __init__(self, message: str = "Connection to Razorpay Test API timed out. Please try again."):
        super().__init__(message, status_code=504)


class RazorpayDuplicatePaymentError(RazorpayIntegrationError):
    """Raised when a duplicate payment is detected and cannot be processed."""
    def __init__(self, payment_id: str):
        super().__init__(f"Payment '{payment_id}' has already been processed and ingested.", status_code=409)


class RazorpayTestClient:
    """
    Dedicated client for Razorpay Test Mode API communication.
    Completely isolated from risk evaluation rules, database schemas, and LLM logic.
    Strictly forbids production credentials.
    """

    def __init__(self):
        self._refresh_credentials()

    def _refresh_credentials(self):
        """Reads credentials from configuration and initializes SDK client."""
        self.key_id = (settings.RAZORPAY_KEY_ID or "").strip()
        self.key_secret = (settings.RAZORPAY_KEY_SECRET or "").strip()
        self.webhook_secret = (settings.RAZORPAY_WEBHOOK_SECRET or "").strip()

        # Reject production keys immediately
        if self.key_id.startswith("rzp_live_"):
            logger.critical("FATAL: Live Razorpay credentials detected ('rzp_live_'). Production credentials are prohibited!")
            self.is_configured = False
            self._client = None
            return

        self.is_configured = bool(
            self.key_id and
            self.key_secret and
            not self.key_id.startswith("rzp_test_placeholder") and
            not self.key_secret.startswith("rzp_test_placeholder")
        )
        self._client = None
        if self.is_configured:
            try:
                self._client = razorpay.Client(auth=(self.key_id, self.key_secret))
            except Exception as e:
                logger.error(f"Failed to initialize Razorpay SDK client: {e}")
                self._client = None

    def _ensure_configured(self):
        """Validates that valid test mode credentials are set and active."""
        # Refresh if configuration changed dynamically
        current_key = (settings.RAZORPAY_KEY_ID or "").strip()
        if current_key.startswith("rzp_live_"):
            raise RazorpayLiveCredentialProhibitedError()

        if not self.is_configured or not self._client:
            raise RazorpayConfigError(
                "Razorpay Test Mode credentials are not configured. "
                "Please configure RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env."
            )

    def fetch_payment_by_id(self, payment_id: str) -> Dict[str, Any]:
        """
        Retrieves a single payment entity from Razorpay Test Mode API.
        Never returns or leaks the API secret.
        """
        if not payment_id or not isinstance(payment_id, str) or not payment_id.strip():
            raise RazorpayInvalidPaymentIdError("A valid payment ID is required.")

        clean_id = payment_id.strip()
        self._ensure_configured()

        try:
            payment = self._client.payment.fetch(clean_id)
            if not payment:
                raise RazorpayPaymentNotFoundError(clean_id)
            if not isinstance(payment, dict):
                raise RazorpayIntegrationError("Malformed response received from Razorpay API.", status_code=502)
            if "id" not in payment or "amount" not in payment:
                raise RazorpayIntegrationError("Malformed payment entity returned from Razorpay API.", status_code=502)
            return payment
        except RazorpayIntegrationError:
            raise
        except requests.exceptions.Timeout:
            logger.error(f"Timeout communicating with Razorpay API for payment {clean_id}")
            raise RazorpayTimeoutError()
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to Razorpay API for payment {clean_id}: {e}")
            raise RazorpayIntegrationError("Could not connect to Razorpay Test API gateway.", status_code=502)
        except razorpay.errors.BadRequestError as e:
            err_msg = str(e)
            logger.warning(f"Razorpay BadRequest for payment {clean_id}: {err_msg}")
            lower_msg = err_msg.lower()
            if "auth" in lower_msg or "unauthorized" in lower_msg or "invalid key" in lower_msg:
                raise RazorpayAuthError()
            if "bad_request_error" in err_msg or "not found" in lower_msg or "does not exist" in lower_msg:
                raise RazorpayPaymentNotFoundError(clean_id)
            raise RazorpayIntegrationError(f"Razorpay API Bad Request: {err_msg}", status_code=400)
        except razorpay.errors.GatewayError as e:
            err_msg = str(e)
            logger.error(f"Razorpay Gateway Error for {clean_id}: {err_msg}")
            if "auth" in err_msg.lower() or "unauthorized" in err_msg.lower():
                raise RazorpayAuthError()
            raise RazorpayIntegrationError(f"Razorpay Gateway Error: {err_msg}", status_code=502)
        except razorpay.errors.ServerError as e:
            logger.error(f"Razorpay Server Error for {clean_id}: {e}")
            raise RazorpayIntegrationError("Razorpay Test API is currently experiencing upstream errors.", status_code=502)
        except Exception as e:
            err_str = str(e)
            lower_str = err_str.lower()
            if "timeout" in lower_str:
                raise RazorpayTimeoutError()
            if "not found" in lower_str or "does not exist" in lower_str or "404" in err_str:
                raise RazorpayPaymentNotFoundError(clean_id)
            if "auth" in lower_str or "unauthorized" in lower_str or "401" in err_str:
                raise RazorpayAuthError()
            logger.error(f"Unexpected error fetching Razorpay payment {clean_id}: {e}")
            raise RazorpayIntegrationError("Failed to communicate with Razorpay API.", status_code=502)

    def create_order(self, amount_in_rupees: float, currency: str = "INR", receipt: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates a Razorpay Test Mode Order.
        Amount is converted to paise (INR * 100).
        """
        amount_paise = int(amount_in_rupees * 100)
        receipt_id = receipt or f"rcpt_{uuid.uuid4().hex[:8]}"

        if self._client:
            try:
                order_data = {
                    "amount": amount_paise,
                    "currency": currency.upper(),
                    "receipt": receipt_id,
                    "payment_capture": 1,
                    "notes": {"source": "RazorGuard_Agent", "mode": "TEST"}
                }
                order = self._client.order.create(data=order_data)
                return {
                    "order_id": order["id"],
                    "amount": amount_in_rupees,
                    "currency": currency,
                    "receipt": receipt_id,
                    "key_id": self.key_id,
                    "mock": False,
                }
            except Exception as exc:
                logger.warning(f"Razorpay API order creation failed: {exc}. Generating mock test order.")

        # Safe fallback mock order if keys are not configured
        mock_order_id = f"order_test_{uuid.uuid4().hex[:14]}"
        return {
            "order_id": mock_order_id,
            "amount": amount_in_rupees,
            "currency": currency,
            "receipt": receipt_id,
            "key_id": self.key_id or "rzp_test_mock_sandbox",
            "mock": True,
        }

    def fetch_payments(self, count: int = 10, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Pulls recent payments from Razorpay Test API.
        """
        if self._client:
            try:
                payments_resp = self._client.payment.all({"count": count, "skip": skip})
                return payments_resp.get("items", [])
            except Exception as exc:
                logger.warning(f"Could not fetch payments from Razorpay API: {exc}")
        return []

    def verify_webhook_signature(self, raw_body: bytes, signature: str) -> bool:
        """
        Cryptographic verification of Razorpay webhook HMAC-SHA256 signature.
        Uses constant-time comparison to prevent timing leaks.
        """
        secret = self.webhook_secret or self.key_secret
        if not secret or not signature:
            return False

        try:
            expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception:
            return False


# Global singleton instance
razorpay_client = RazorpayTestClient()
