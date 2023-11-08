import logging
import traceback

from integration.repository import IntegrationRepository
from integration.services import (
    AsanaService,
    FigmaService,
    GithubService,
    GoogleService,
    MicrosoftService,
    NotionService,
    SlackService,
)
from integration.services.base import BaseService

logger = logging.getLogger(__name__)


def check_integration_status(service_class: BaseService, user_integration):
    """
    Check the status of a user's integration.

    Args:
    - service_class: The service class to use for checking.
    - user_integration: The user integration record.

    Returns:
    - bool: True if integration is active, False otherwise.
    """
    try:
        meta_data = IntegrationRepository.decrypt_meta_data(
            meta_data=user_integration.meta_data
        )
        return service_class().is_active(
            meta_data, user_integration_id=user_integration.id
        )
    except Exception:
        return False


def main():
    try:
        user_integrations = IntegrationRepository.fetch_all_user_integrations()
        revoked_integrations = []
        for user_integration in user_integrations:
            try:
                service_class = None
                if user_integration.integration.name == "Gmail":
                    service_class = GoogleService
                elif user_integration.integration.name == "GitHub":
                    service_class = GithubService
                elif user_integration.integration.name == "Slack":
                    service_class = SlackService
                elif user_integration.integration.name == "Notion":
                    service_class = NotionService
                elif user_integration.integration.name == "Figma":
                    service_class = FigmaService
                elif user_integration.integration.name == "Outlook":
                    service_class = MicrosoftService
                elif user_integration.integration.name == "Asana":
                    service_class = AsanaService
                if service_class:
                    is_active = check_integration_status(
                        service_class, user_integration
                    )
                    if not is_active:
                        revoked_integrations.append(user_integration.id)
            except Exception:
                logger.exception(
                    f"An error occurred while checking integration status for user {user_integration.user.email}.",
                    extra={
                        "traceback": traceback.format_exc(),
                    },
                )
        IntegrationRepository.revoke_user_integrations(revoked_integrations)
    except Exception:
        logger.exception(
            f"An error occurred while revoking integrations.",
            extra={
                "traceback": traceback.format_exc(),
            },
        )
