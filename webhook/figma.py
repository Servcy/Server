import json
import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from inbox.repository import InboxRepository
from integration.repository import IntegrationRepository

logger = logging.getLogger(__name__)


def get_title(event: dict):
    event_type = event["event_type"]
    if event_type == "FILE_UPDATE":
        return f"{event['file_name']} file was updated"
    elif event_type == "FILE_DELETE":
        return f"{event['file_name']} file was deleted"
    elif event_type == "FILE_VERSION_UPDATE":
        return f"{event['file_name']} file version was updated"
    elif event_type == "FILE_COMMENT":
        return f"{event['file_name']} file was commented on"
    elif event_type == "LIBRARY_PUBLISH":
        return f"{event['library_name']} library was published"
    else:
        raise ValueError(f"Unknown event type: {event_type}")


@csrf_exempt
@require_POST
def figma(request):
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
        InboxRepository.add_items(
            [
                {
                    "title": get_title(body),
                    "cause": body.get("triggered_by", {}).get("handle", "-"),
                    "body": json.dumps(body),
                    "is_body_html": False,
                    "user_integration_id": user_integration.id,
                    "uid": f"{body['webhook_id']}-{user_integration.id}",
                    "category": "comment"
                    if "FILE_COMMENT" == body["event_type"]
                    else "notification",
                }
            ]
        )
        return HttpResponse(status=200)
    except Exception as err:
        logger.exception(
            f"An error occurred while processing figma webhook.", exc_info=True
        )
        return HttpResponse(status=500)
