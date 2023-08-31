from integration.repository import IntegrationRepository
from integration.services import (
    FigmaService,
    GithubService,
    GoogleService,
    MicrosoftService,
    NotionService,
    SlackService,
)
from integration.services.base import BaseService


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
        return service_class().is_active(meta_data)
    except Exception:
        return False


def main():
    user_integrations = IntegrationRepository.fetch_all_user_integrations()
    revoked_integrations = []
    for user_integration in user_integrations:
        service_class = None
        if user_integration.integration.name == "Google":
            service_class = GoogleService
        elif user_integration.integration.name == "GitHub":
            service_class = GithubService
        elif user_integration.integration.name == "Slack":
            service_class = SlackService
        elif user_integration.integration.name == "Notion":
            service_class = NotionService
        elif user_integration.integration.name == "Figma":
            service_class = FigmaService
        elif user_integration.integration.name == "Microsoft":
            service_class = MicrosoftService
        if service_class:
            is_active = check_integration_status(service_class, user_integration)
            if not is_active:
                revoked_integrations.append(user_integration)
    IntegrationRepository.revoke_integrations(revoked_integrations)
