from django.conf import settings
from twilio.rest import Client


def send_authentication_code_email(client: Client, email: str) -> None:
    client.verify.services(settings.TWILLIO_VERIFY_SERVICE_ID).verifications.create(
        channel_configuration={
            "template_id": settings.SENDGRID_VERIFICATION_TEMPLATE_ID,
            "from": settings.SENDGRID_FROM_EMAIL,
            "from_name": "Servcy",
        },
        to=email,
        channel="email",
    )


def send_authentication_code_phone(
    client: Client, phone_number: str, is_whatsapp: bool
) -> None:
    client.verify.services(settings.TWILLIO_VERIFY_SERVICE_ID).verifications.create(
        to=f"+{phone_number}",
        channel="sms" if not is_whatsapp else "whatsapp",
    )
