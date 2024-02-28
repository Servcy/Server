import logging
import traceback

from integration.repository import IntegrationRepository
from integration.services.jira import JiraService

logger = logging.getLogger(__name__)


def refresh_webhooks_and_tokens():
    """
    Refreshes Jira webhooks and tokens.
    """

    try:
        user_integrations = IntegrationRepository.get_user_integrations(
            {
                "integration__name": "Jira",
            }
        )
        for user_integration in user_integrations:
            try:
                jira_service = JiraService(
                    token=user_integration["meta_data"]["token"],
                    cloud_id=user_integration["meta_data"]["cloud_id"],
                )
                jira_service.extend_webhook()
                new_tokens = jira_service.refresh_token()
                IntegrationRepository.update_integraion_meta_data(
                    user_integration_id=user_integration["id"],
                    meta_data={
                        **user_integration["meta_data"],
                        "token": {
                            **user_integration["meta_data"]["token"],
                            **new_tokens,
                        },
                    },
                )
            except:
                logger.exception(
                    f"Error in refreshing webhooks and tokens for Jira",
                    extra={
                        "traceback": traceback.format_exc(),
                    },
                )
                continue
    except Exception:
        logger.exception(
            f"Error in refreshing webhooks and tokens for Jira",
            extra={
                "traceback": traceback.format_exc(),
            },
        )
