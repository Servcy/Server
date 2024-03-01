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
    "jira:issue_created": "Issue: {issue_name} [Created]",
    "jira:issue_updated": "Issue: {issue_name} [Updated]",
    "jira:issue_deleted": "Issue: {issue_name} [Deleted]",
    "comment_created": "Comment: {comment_summary} Issue: {issue_name} [Created]",
    "comment_updated": "Comment: {comment_summary} Issue: {issue_name} [Updated]",
    "comment_deleted": "Comment: {comment_summary} Issue: {issue_name} [Deleted]",
}


@csrf_exempt
@require_POST
def jira(request):
    try:
        headers = request.headers
        body = json.loads(request.body)
        account_id = None
        if body.get("webhookEvent") not in EVENT_MAP.keys():
            return HttpResponse(status=200)
        if "issue" in body["webhookEvent"]:
            account_id = body["issue"]["fields"]["assignee"]["accountId"]
        elif "comment" in body["webhookEvent"]:
            account_id = body["comment"]["author"]["accountId"]
        else:
            account_id = body.get("user", {}).get("accountId")
        user_integration = IntegrationRepository.get_user_integrations(
            filters={
                "integration__name": "Jira",
                "account_id": account_id,
            },
            first=True,
        )
        if not user_integration:
            return HttpResponse(status=200)
        disabled_events = (
            DisabledUserIntegrationEventRepository.get_disabled_user_integration_events(
                user_integration_id=user_integration["id"]
            )
        )
        if is_event_and_action_disabled(disabled_events, body["webhookEvent"], None):
            return HttpResponse(status=200)
        if "issue" in body["webhookEvent"]:
            issue_name = (
                body.get("issue", {}).get("fields", {}).get("summary", "Unknown")
            )
            sender = body["user"]
            title = EVENT_MAP[body["webhookEvent"]].format(issue_name=issue_name)
        elif "comment" in body["webhookEvent"]:
            issue_name = (
                body.get("issue", {}).get("fields", {}).get("summary", "Unknown")
            )
            comment_summary = (
                body.get("comment", {}).get("body", "Unknown")[:50] + "..."
            )
            title = EVENT_MAP[body["webhookEvent"]].format(
                issue_name=issue_name, comment_summary=comment_summary
            )
            sender = body["comment"]["author"]
        else:
            title = "Jira event"
            sender = body.get("user")
        InboxRepository.add_item(
            {
                "title": title,
                "cause": json.dumps(sender),
                "body": json.dumps(body),
                "is_body_html": False,
                "user_integration_id": user_integration["id"],
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
