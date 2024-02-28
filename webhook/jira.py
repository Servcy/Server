import json
import logging
import traceback
import uuid

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from inbox.repository import InboxRepository
from integration.repository import IntegrationRepository
from integration.repository.events import DisabledUserIntegrationEventRepository
from integration.utils.events import is_event_and_action_disabled

logger = logging.getLogger(__name__)

EVENT_MAP = {
    "jira:issue_created": "An issue was created on Jira",
    "jira:issue_updated": "An issue was updated on Jira",
    "jira:issue_deleted": "An issue was deleted on Jira",
    "comment_created": "A comment was added on Jira",
    "comment_updated": "A comment was updated on Jira",
    "comment_deleted": "A comment was deleted on Jira",
}


@csrf_exempt
@require_POST
def jira(request):
    try:
        headers = request.headers
        body = json.loads(request.body)
        user_integration = IntegrationRepository.get_user_integrations(
            filters={
                "integration__name": "Jira",
                "account_id": body["user"]["accountId"],
            },
            first=True,
        )
        disabled_events = (
            DisabledUserIntegrationEventRepository.get_disabled_user_integration_events(
                user_integration_id=user_integration.id
            )
        )
        if is_event_and_action_disabled(disabled_events, body["webhookEvent"], None):
            return HttpResponse(status=200)
        if "issue" in body["webhookEvent"]:
            sender = body["user"]
        elif "comment" in body["webhookEvent"]:
            sender = body["comment"]["author"]
        else:
            sender = body.get("user")
        InboxRepository.add_item(
            {
                "title": EVENT_MAP.get(body["webhookEvent"], "Jira event"),
                "cause": json.dumps(sender),
                "body": json.dumps(body),
                "is_body_html": False,
                "user_integration_id": user_integration.id,
                "uid": str(uuid.uuid4()),
                "category": (
                    "comment" if "comment" in body["webhookEvent"] else "notification"
                ),
                "i_am_mentioned": True,
            }
        )
        return HttpResponse(status=200)
    except Exception:
        logger.exception(
            f"An error occurred while processing jira webhook.",
            extra={
                "body": body,
                "headers": headers,
                "traceback": traceback.format_exc(),
            },
        )
        return HttpResponse(status=500, content="Internal Server Error")
