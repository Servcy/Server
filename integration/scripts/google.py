import logging
import traceback

from integration.repository import IntegrationRepository
from integration.services.google import GoogleService

logger = logging.getLogger(__name__)


def refresh_watchers_and_tokens():
    """
    Refresh watchers for all users in the system.
    """
    try:
        user_integrations = IntegrationRepository.get_user_integrations(
            {
                "integration__name": "Gmail",
            }
        )
        for user_integration in user_integrations:
            try:
                google_service = GoogleService(
                    access_token=user_integration["meta_data"]["token"]["access_token"],
                    refresh_token=user_integration["meta_data"]["token"][
                        "refresh_token"
                    ],
                )
                google_service._fetch_user_info_from_service()
                google_service._add_watcher_to_inbox_pub_sub(
                    google_service._user_info["emailAddress"]
                )
                new_tokens = google_service.refresh_tokens()
                IntegrationRepository.update_integraion(
                    user_integration_id=user_integration["id"],
                    meta_data=IntegrationRepository.encrypt_meta_data(
                        {
                            **user_integration["meta_data"],
                            "token": {
                                **user_integration["meta_data"]["token"],
                                **new_tokens,
                            },
                        }
                    ),
                )
            except:
                logger.exception(
                    f"Error in refreshing watchers for gmail for user integration {user_integration['id']}",
                    extra={
                        "traceback": traceback.format_exc(),
                    },
                )
                continue
    except Exception:
        logger.exception(
            f"Error in refreshing watchers for gmail.",
            extra={
                "traceback": traceback.format_exc(),
            },
        )
