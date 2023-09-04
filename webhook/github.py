import json
import logging
import traceback

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from inbox.repository import InboxRepository
from integration.repository import IntegrationRepository
from integration.services.github import GithubService

logger = logging.getLogger(__name__)

VALID_EVENTS = [
    "issues",
    "project_card",
    "projects_v2_item",
    "pull_request",
    "pull_request_review_thread",
    "pull_request_review_comment",
    "pull_request_review",
    "project_column",
    "project",
    "milestone",
    "issue_comment",
]


@csrf_exempt
@require_POST
def github(request):
    try:
        payload = json.loads(request.body)
        event = request.headers.get("X-GitHub-Event", "ping")
        if event == "ping":
            return HttpResponse(status=200)
        if event == "installation":
            GithubService.manage_github_configuration(payload)
            return HttpResponse(status=200)
        if event not in VALID_EVENTS:
            logger.info(f"Received invalid github event: {event} - {payload}")
            return HttpResponse(status=200)
        installation_id = payload["installation"]["id"]
        user_integration = IntegrationRepository.get_user_integration(
            {"integration__name": "Github", "configuration__contains": installation_id}
        )
        InboxRepository.add_items(
            [
                {
                    "title": f"{' '.join(event.split('_'))} {' '.join(payload.get('action', '').split('_'))}",
                    "cause": payload["sender"]["login"],
                    "body": json.dump(payload),
                    "is_body_html": False,
                    "user_integration_id": user_integration.id,
                    "uid": f"{request.headers['X-GitHub-Delivery']}-{user_integration.id}",
                }
            ]
        )
        return HttpResponse(status=200)
    except Exception:
        logger.error(
            f"An error occurred while processing github webhook.\n{traceback.format_exc()}"
        )
        return HttpResponse(status=500)
