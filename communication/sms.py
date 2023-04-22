import logging
import traceback

from django.conf import settings
from twilio.rest import Client


logger = logging.getLogger(__name__)


def send_sms(to: str, body: str) -> None:
    """
    Send an SMS to given number with given body
    Parameters
    ----------
    to : str
    body : str
    Returns
    -------
    None
    """
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(to=to, from_=settings.TWILIO_NUMBER, body=body)
    except Exception as err:
        logger.error(f"Error sending SMS: {traceback.format_exc()}")
        raise err
