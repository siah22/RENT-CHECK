import base64
import json
import logging
import uuid

import requests
from django.conf import settings

from .models import Payment

logger = logging.getLogger(__name__)


class MpesaError(Exception):
    pass


def _configured():
    return bool(settings.MPESA_API_KEY and settings.MPESA_PUBLIC_KEY)


def _truncate(value, length):
    value = str(value or "")
    return value[:length]


def _encrypt_api_key():
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.serialization import load_der_public_key

    public_key = settings.MPESA_PUBLIC_KEY.strip()
    der = base64.b64decode(public_key.replace(" ", ""))
    pub = load_der_public_key(der)
    encrypted = pub.encrypt(settings.MPESA_API_KEY.encode(), padding.PKCS1v15())
    return base64.b64encode(encrypted).decode()


def _session():
    env = settings.MPESA_ENVIRONMENT
    url = f"{settings.MPESA_BASE_URL}/{env}/ipg/v2/{settings.MPESA_MARKET}/getSession/"
    response = requests.post(
        url,
        data=json.dumps({"input_ApiKey": _encrypt_api_key()}),
        headers={"Origin": settings.MPESA_ORIGIN, "Content-Type": "application/json"},
        timeout=settings.MPESA_TIMEOUT,
    )
    payload = response.json()
    if str(payload.get("output_ResponseCode", "")).endswith("000000") and payload.get("output_SessionID"):
        return payload["output_SessionID"]
    raise MpesaError(f"getSession failed: {payload.get('output_ResponseDesc', response.text)}")


def initiate_payment(user, amount, purpose, reference, phone, description=""):
    """Create a Payment and push a C2B single-stage request to the customer's phone.

    Without MPESA_API_KEY (development/demo) the payment is completed immediately
    and recorded as SIMULATED so the whole flow stays testable.
    """
    conversation_id = uuid.uuid4().hex
    payment = Payment.objects.create(
        user=user,
        amount=amount,
        purpose=purpose,
        reference=_truncate(reference, 120),
        description=_truncate(description, 255),
        phone=phone,
        conversation_id=conversation_id,
    )

    if not _configured():
        payment.status = Payment.Status.COMPLETED
        payment.transaction_id = "SIMULATED-" + conversation_id[:16]
        payment.provider_response = {"mode": "simulated"}
        payment.save(update_fields=["status", "transaction_id", "provider_response", "updated_at"])
        logger.info("PAYMENT [simulated]: %s TZS purpose=%s ref=%s", amount, purpose, reference)
        return payment

    try:
        session = _session()
        env = settings.MPESA_ENVIRONMENT
        url = f"{settings.MPESA_BASE_URL}/{env}/ipg/v2/{settings.MPESA_MARKET}/c2bPayment/singleStage/"
        body = {
            "input_Amount": str(int(payment.amount)),
            "input_Country": settings.MPESA_COUNTRY,
            "input_Currency": settings.MPESA_CURRENCY,
            "input_CustomerMSISDN": phone,
            "input_ServiceProviderCode": settings.MPESA_SERVICE_PROVIDER_CODE,
            "input_ThirdPartyConversationID": payment.conversation_id,
            "input_TransactionReference": f"RC{payment.pk:07d}",
            "input_PurchasedItemsDesc": _truncate(reference, 30),
        }
        headers = {
            "Origin": settings.MPESA_ORIGIN,
            "Content-Type": "application/json",
            "Authorization": f"Bearer {session}",
        }
        response = requests.post(url, data=json.dumps(body), headers=headers, timeout=settings.MPESA_TIMEOUT)
        payload = response.json()
        payment.provider_response = payload
        if str(payload.get("output_ResponseCode", "")).endswith("000000"):
            payment.transaction_id = payload.get("output_TransactionID", "")
            payment.status = Payment.Status.PENDING
            message = "Payment request sent — approve it on your phone."
        else:
            payment.status = Payment.Status.FAILED
            message = payload.get("output_ResponseDesc", "M-Pesa rejected the request.")
        payment.save(update_fields=["status", "transaction_id", "provider_response", "updated_at"])
        return payment
    except Exception as exc:  # noqa: BLE001 — never crash the request on provider trouble
        logger.exception("M-Pesa initiation failed for payment %s", payment.pk)
        payment.status = Payment.Status.FAILED
        payment.provider_response = {"error": str(exc)}
        payment.save(update_fields=["status", "provider_response", "updated_at"])
        return payment


def query_status(payment):
    """Ask M-Pesa for the latest status; reconciles COMPLETED on a positive result."""
    if not _configured() or payment.status != Payment.Status.PENDING:
        return payment
    try:
        session = _session()
        env = settings.MPESA_ENVIRONMENT
        url = f"{settings.MPESA_BASE_URL}/{env}/ipg/v2/{settings.MPESA_MARKET}/queryTransactionStatus/"
        body = {
            "input_QueryReference": payment.transaction_id,
            "input_ServiceProviderCode": settings.MPESA_SERVICE_PROVIDER_CODE,
            "input_ThirdPartyConversationID": uuid.uuid4().hex,
            "input_Country": settings.MPESA_COUNTRY,
        }
        headers = {
            "Origin": settings.MPESA_ORIGIN,
            "Content-Type": "application/json",
            "Authorization": f"Bearer {session}",
        }
        response = requests.post(url, data=json.dumps(body), headers=headers, timeout=settings.MPESA_TIMEOUT)
        payload = response.json()
        payment.provider_response = payload
        description = " ".join(str(payload.get(k, "")) for k in (
            "output_ResponseDesc", "output_TransactionStatus", "output_ResponseCode"))
        code = str(payload.get("output_ResponseCode", ""))
        if "success" in description.lower() or "completed" in description.lower() or code.endswith("000000"):
            payment.status = Payment.Status.COMPLETED
        payment.save(update_fields=["status", "provider_response", "updated_at"])
    except Exception as exc:  # noqa: BLE001
        logger.exception("M-Pesa status query failed for payment %s", payment.pk)
        payment.provider_response["error"] = str(exc)
        payment.save(update_fields=["provider_response", "updated_at"])
    return payment


def confirm_from_callback(payload):
    """Reconcile a payment from the M-Pesa C2B confirmation callback."""
    conversation_id = payload.get("input_ThirdPartyConversationID") or ""
    transaction = payload.get("input_TransactionID") or ""
    reference = payload.get("input_TransactionReference") or ""

    payment = Payment.objects.filter(conversation_id=conversation_id).first()
    if payment is None and reference.startswith("RC"):
        payment = Payment.objects.filter(pk=int(reference[2:].lstrip("0") or 0)).first()

    if payment is None:
        logger.warning("M-Pesa callback for unknown payment: %s", payload)
        return None

    payment.transaction_id = transaction
    payment.provider_response = payload
    payment.status = Payment.Status.COMPLETED
    payment.save(update_fields=["status", "transaction_id", "provider_response", "updated_at"])
    logger.info("Payment %s confirmed via callback (%s TZS)", payment.pk, payment.amount)
    return payment