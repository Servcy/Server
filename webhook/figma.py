import json
import logging
import traceback

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from inbox.repository import InboxRepository
from integration.repository import IntegrationRepository
from integration.repository.events import DisabledUserIntegrationEventRepository
from integration.utils.events import is_event_and_action_disabled

logger = logging.getLogger(__name__)


def get_title(event: dict):
    event_type = event["event_type"]
    if event_type == "FILE_UPDATE":
        return f"{event['file_name']} [Updated]"
    elif event_type == "FILE_DELETE":
        return f"{event['file_name']} [Deleted]"
    elif event_type == "FILE_VERSION_UPDATE":
        return f"{event['file_name']} [Version Updated]"
    elif event_type == "FILE_COMMENT":
        return f"{event['file_name']} [Comment Added]"
    elif event_type == "LIBRARY_PUBLISH":
        return f"{event['library_name']} [Library Published]"
    else:
        raise ValueError(f"Unknown event type: {event_type}")


@csrf_exempt
@require_POST
def figma(request):
    """
    Figma webhook endpoint:
    - Receives a request from Figma
    - Validates the request
    - Saves the request to the inbox
    """
    try:
        body = json.loads(request.body)
        if body["event_type"] == "PING":
            return HttpResponse(status=200)
        user_integration = IntegrationRepository.get_user_integrations(
            filters={
                "id": int(body["passcode"]),
                "integration__name": "Figma",
            },
            first=True,
        )
        disabled_events = (
            DisabledUserIntegrationEventRepository.get_disabled_user_integration_events(
                user_integration_id=user_integration["id"]
            )
        )
        if is_event_and_action_disabled(disabled_events, body["event_type"], None):
            return HttpResponse(status=200)
        i_am_mentioned = False
        if body["event_type"] == "FILE_COMMENT":
            for comment in body["comments"]:
                for mention in comment["mentions"]:
                    if mention["id"] == user_integration["account_id"]:
                        i_am_mentioned = True
                        break
        InboxRepository.add_item(
            {
                "title": get_title(body),
                "cause": body.get("triggered_by", {}).get("handle", "-"),
                "body": json.dumps(body),
                "is_body_html": False,
                "user_integration_id": user_integration["id"],
                "uid": body["webhook_id"],
                "category": (
                    "comment"
                    if "FILE_COMMENT" == body["event_type"]
                    else "notification"
                ),
                "i_am_mentioned": i_am_mentioned,
            }
        )
        return HttpResponse(status=200)
    except Exception:
        logger.exception(
            f"An error occurred while processing figma webhook.",
            extra={
                "body": body,
                "headers": request.headers,
                "traceback": traceback.format_exc(),
            },
        )
        return HttpResponse(status=500)
