import logging
import traceback
import uuid

from django.conf import settings

from inbox.repository import InboxRepository
from integration.repository import IntegrationRepository
from integration.services.base import BaseService
from integration.utils.maps import integration_service_map

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
        inbox_items = []
        for user_integration in user_integrations:
            try:
                integration_name = user_integration.integration.name
                service_class = integration_service_map.get(integration_name)
                if service_class is None:
                    continue
                is_active = check_integration_status(service_class, user_integration)
                if not is_active:
                    revoked_integrations.append(user_integration)
            except Exception:
                logger.exception(
                    f"An error occurred while checking integration status for user {user_integration.user.email}.",
                    extra={
                        "traceback": traceback.format_exc(),
                    },
                )
        for revoked_integration in revoked_integrations:
            inbox_items.append(
                {
                    "title": f"An integration has been revoked, please re-authenticate.",
                    "cause": None,
                    "body": f"""<div style="margin-left: 10px; font-family: monospace;"><table><tr><td>Integration Name</td><td style="padding-left: 16px; font-weight: 600;">{revoked_integration.integration.name}</td></tr><tr><td>Account</td><td style="padding-left: 16px; font-weight: 600;">{revoked_integration.account_display_name}</td></tr></table><div style="margin: 10px 0;"><a style="color: #26542F; text-decoration: underline;" href="{settings.FRONTEND_URL}/integrations?integration={revoked_integration.integration.id}">Click here</a> to re-authenticate.</div></div>""",
                    "is_body_html": True,
                    "user_integration_id": revoked_integration.id,
                    "uid": str(uuid.uuid4()),
                    "category": "notification",
                    "i_am_mentioned": True,
                }
            )
        IntegrationRepository.revoke_user_integrations(
            [revoked_integration.id for revoked_integration in revoked_integrations]
        )
        InboxRepository.add_items(inbox_items)
    except Exception:
        logger.exception(
            f"An error occurred while revoking integrations.",
            extra={
                "traceback": traceback.format_exc(),
            },
        )
