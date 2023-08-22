import datetime
import logging
import traceback

from integration.repository import IntegrationRepository
from integration.services.microsoft import MicrosoftService

logger = logging.getLogger(__name__)


def renew_microsoft_subscriptions():
    """
    This function is used to renew the Microsoft subscriptions.
    """
    microsoft_integrations = IntegrationRepository.get_user_integrations(
        {
            "integration__name": "Outlook",
        }
    )
    for integration in microsoft_integrations:
        try:
            subscription = integration["meta_data"]["subscription"]
            expiration_date_time = datetime.datetime.strptime(
                subscription["expirationDateTime"], "%Y-%m-%dT%H:%M:%SZ"
            )
            if (expiration_date_time - datetime.datetime.now()).total_seconds() < 86400:
                MicrosoftService(
                    refresh_token=integration["meta_data"]["token"]["refresh_token"]
                ).renew_subscription(subscription["id"])
        except Exception:
            logger.error(
                f"An error occurred while renewing subscription for user {integration['user_id']}.\n{traceback.format_exc()}"
            )
