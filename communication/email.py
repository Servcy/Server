import json
import logging
import traceback

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_email(
    to_email: str, subject: str, html_content: str, user_name: str = None
) -> requests.Response:
    """
    Send email to user with html content
    Parameters
    ----------
    to_email : str
    subject : str
    html_content : str
    user_name : str
    Returns
    -------
    requests.Response
    """
    try:
        personalizations_to = {"email": to_email}
        if user_name:
            personalizations_to["name"] = user_name
        payload = {
            "personalizations": [
                {
                    "to": [personalizations_to],
                    "subject": subject,
                }
            ],
            "content": [
                {"type": "text/html", "value": html_content},
            ],
            "from": {
                "email": "contact@servcy.com",
                "name": "Support Team Servcy",
            },
            "reply_to": {
                "email": "contact@servcy.com",
                "name": "Support Team Servcy",
            },
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
        }
        response = requests.request(
            "POST",
            settings.SEND_EMAIL_ENDPOINT,
            headers=headers,
            data=json.dumps(payload),
        )
        return response
    except Exception as err:
        logger.error(f"Error sending email: {traceback.format_exc()}")
        raise err
