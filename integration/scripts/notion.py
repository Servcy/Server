import json
import logging
import traceback

from django.db import transaction

from inbox.services import InboxRepository
from integration.repository import IntegrationRepository
from integration.services.notion import NotionService

logger = logging.getLogger(__name__)


def poll_new_comments():
    try:
        user_integrations = IntegrationRepository.get_user_integrations(
            {
                "integration__name": "Notion",
            }
        )
        inbox_items = []
        configuration_map = {}
        for user_integration in user_integrations:
            try:
                process_user_integration(
                    user_integration, inbox_items, configuration_map
                )
            except Exception:
                logger.exception(
                    f"An error occurred while fetching notion comments for user {user_integration['user_id']}",
                    extra={
                        "traceback": traceback.format_exc(),
                    },
                )
        with transaction.atomic():
            InboxRepository.add_items(inbox_items)
            for user_integration_id, configuration in configuration_map.items():
                IntegrationRepository.update_integraion_configuration(
                    user_integration_id, configuration=configuration
                )
    except Exception:
        logger.exception(
            "An error occurred while fetching notion comments",
            extra={
                "traceback": traceback.format_exc(),
            },
        )


def process_user_integration(
    user_integration: dict, inbox_items: list, configuration_map: dict
):
    """
    Process a user integration for new comments.
    """
    configuration_map[user_integration["id"]] = user_integration["configuration"]
    service = NotionService(token=user_integration["meta_data"]["token"])
    pages = user_integration["configuration"]["pages"]
    users = service.fetch_all_users()
    user_map = {user["id"]: user for user in users}

    for i, page in enumerate(pages):
        try:
            process_page(
                i,
                page,
                user_integration,
                service,
                user_map,
                inbox_items,
                configuration_map,
            )
        except Exception:
            logger.exception(
                f"An error occurred while fetching notion comments for page {page['page_id']}",
                extra={
                    "traceback": traceback.format_exc(),
                },
            )


def process_page(
    i: int,
    page: dict,
    user_integration: dict,
    service: "NotionService",
    user_map: dict[str, dict],
    inbox_items: list,
    configuration_map: dict,
):
    """
    Process a page for new comments.
    """
    comments = service.get_new_unresolved_comments(
        page["page_id"], page.get("last_cursor", "")
    )
    if comments:
        comment_from = user_map.get(comments[0]["created_by"]["id"])
        for comment in comments:
            i_am_mentioned = False
            for block in comment.get("rich_text", []):
                if (
                    block["type"] == "mention"
                    and block["mention"]["type"] == "user"
                    and block["mention"]["user"]["id"] == user_integration["account_id"]
                ):
                    i_am_mentioned = True
                    break
            inbox_items.append(
                {
                    "title": f"New comment on {page['page_name']}",
                    "cause": json.dumps(comment_from),
                    "body": json.dumps(comment),
                    "is_body_html": False,
                    "user_integration_id": user_integration["id"],
                    "uid": comment["id"],
                    "category": "comment",
                    "i_am_mentioned": i_am_mentioned,
                }
            )
        configuration_map[user_integration["id"]]["pages"][i]["last_cursor"] = comments[
            -1
        ]["id"]
