import logging

from django.conf import settings

from .models import Notification

logger = logging.getLogger(__name__)


def notify(user, message, link="", subject=""):
    """Create the in-app notification and fan out to email + SMS.

    Email and SMS silently no-op when the recipient has no contact details or the
    provider is unconfigured, so a delivery failure never breaks a request.
    """
    Notification.objects.create(user=user, message=message, link=link)

    email = (getattr(user, "email", "") or "").strip()
    if email:
        try:
            send_email_message(subject or "RentCheck notification", message, email, link)
        except Exception:
            logger.exception("Email delivery failed to %s", email)

    phone = (getattr(user, "phone_number", "") or "").strip()
    if phone:
        try:
            send_sms_message(message, phone)
        except Exception:
            logger.exception("SMS delivery failed to %s", phone)


def send_email_message(subject, message, email, link=""):
    from django.core.mail import send_mail

    body = message
    if link:
        absolute_link = link if link.startswith("http") else settings.SITE_BASE_URL + link
        body = f"{message}\n\n{absolute_link}"
    body += "\n\nSent by RentCheck Tanzania"
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=True)


def send_sms_message(message, phone):
    import requests

    phone = _normalize_phone(phone)
    if not phone:
        return

    provider = settings.SMS_PROVIDER
    if not settings.SMS_API_KEY:
        logger.info("SMS (console, %s not configured): %s -> %s", provider, phone, message)
        return

    if provider == "twilio":
        _send_twilio_sms(phone, message)
    elif provider == "africastalking":
        _send_africastalking_sms(phone, message)
    else:
        logger.info("SMS (console): %s -> %s", phone, message)


def _normalize_phone(phone):
    phone = (phone or "").strip().replace(" ", "").replace("-", "")
    if not phone:
        return ""
    if phone.startswith("+"):
        return phone
    if phone.startswith("0") and len(phone) == 10:
        return "+255" + phone[1:]
    if phone.startswith("255") and len(phone) == 12:
        return "+" + phone
    return phone


def _send_twilio_sms(to, message):
    import requests

    sid = settings.TWILIO_ACCOUNT_SID
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    requests.post(
        url,
        auth=(sid, settings.TWILIO_AUTH_TOKEN),
        data={"From": settings.TWILIO_FROM_NUMBER, "To": to, "Body": message},
        timeout=10,
    ).raise_for_status()


def _send_africastalking_sms(to, message):
    import requests

    payload = {"username": settings.AT_SMS_USERNAME, "to": to, "message": message}
    if settings.AT_SMS_FROM:
        payload["from"] = settings.AT_SMS_FROM
    requests.post(
        "https://api.africastalking.com/version1/messaging",
        data=payload,
        headers={
            "apiKey": settings.SMS_API_KEY,
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        timeout=10,
    ).raise_for_status()