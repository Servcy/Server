import logging
import traceback

from google.cloud import pubsub_v1

from integration.repository import IntegrationRepository
from integration.services.google import GOOGLE_PUB_SUB_TOPIC, GoogleService

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


def add_publisher_from_topic(email: str):
    """Add publisher for user"""
    try:
        pubsub_v1_client = pubsub_v1.PublisherClient()
        policy = pubsub_v1_client.get_iam_policy(
            request={"resource": GOOGLE_PUB_SUB_TOPIC}
        )
        policy.bindings.add(
            role="roles/pubsub.publisher",
            members=[f"user:{email}"],
        )
        pubsub_v1_client.set_iam_policy(
            request={"resource": GOOGLE_PUB_SUB_TOPIC, "policy": policy}
        )
    except:
        pass


def remove_publisher_from_topic(email: str):
    """Remove publisher for user"""
    try:
        pubsub_v1_client = pubsub_v1.PublisherClient()
        policy = pubsub_v1_client.get_iam_policy(
            request={"resource": GOOGLE_PUB_SUB_TOPIC}
        )
        for binding in policy.bindings:
            if (
                binding.role == "roles/pubsub.publisher"
                and f"user:{email}" in binding.members
            ):
                binding.members.remove(f"user:{email}")
        pubsub_v1_client.set_iam_policy(
            request={"resource": GOOGLE_PUB_SUB_TOPIC, "policy": policy}
        )
    except:
        pass
