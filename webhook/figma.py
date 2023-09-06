import json
import logging
import traceback

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from inbox.repository import InboxRepository
from integration.repository import IntegrationRepository

logger = logging.getLogger(__name__)

EVENT_MAP = {
    "FILE_UPDATE": "A file was updated",
    "FILE_DELETE": "A file was deleted",
    "FILE_VERSION_UPDATE": "A file version was updated",
    "FILE_COMMENT": "A file was commented on",
    "LIBRARY_PUBLISH": "A library was published",
}


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
                    "title": EVENT_MAP[body["event"]["type"]],
                    "cause": body.get("triggered_by", {}).get("handle", "Unknown"),
                    "body": json.dumps(body),
                    "is_body_html": False,
                    "user_integration_id": user_integration.id,
                    "uid": f"{body['webhook_id']}-{user_integration.id}",
                }
            ]
        )
        return HttpResponse(status=200)
    except Exception:
        logger.error(
            f"An error occurred while processing figma webhook.\n{traceback.format_exc()}"
        )
        return HttpResponse(status=500)
