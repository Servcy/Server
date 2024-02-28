import logging
import time
import traceback

from integration.repository import IntegrationRepository
from integration.services.slack import SlackService

logger = logging.getLogger(__name__)


def update_workspace_members():
    """
    Runs as a cron
    """
    try:
        user_integrations = IntegrationRepository.get_user_integrations(
            {"integration__name": "Slack"}
        )
        for user_integration in user_integrations:
            try:
                members = SlackService(
                    token=user_integration["meta_data"]["token"]
                ).fetch_team_members()
                IntegrationRepository.update_integraion_configuration(
                    user_integration["id"], configuration=members
                )
                time.sleep(60)
            except Exception:
                logger.exception(
                    f"An error occurred while updating slack members for user {user_integration['user_id']}.",
                    extra={
                        "traceback": traceback.format_exc(),
                    },
                )
    except Exception:
        logger.exception(
            f"An error occurred while updating slack members.",
            extra={
                "traceback": traceback.format_exc(),
            },
        )
