import hashlib
import hmac
import json
import logging
import traceback

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from common.exceptions import ExternalIntegrationException
from inbox.repository import InboxRepository
from integration.repository import IntegrationRepository
from integration.repository.events import DisabledUserIntegrationEventRepository
from integration.services.github import GithubService
from integration.utils.events import is_event_and_action_disabled

logger = logging.getLogger(__name__)

VALID_EVENTS = [
    "issues",
    "pull_request",
    "pull_request_review_thread",
    "pull_request_review_comment",
    "pull_request_review",
    "issue_comment",
]


def verify_signature(payload_body, secret_token, signature_header):
    """Verify that the payload was sent from GitHub by validating SHA256.

    Raise and return 403 if not authorized.

    Args:
        payload_body: original request body to verify (request.body())
        secret_token: GitHub app webhook token (WEBHOOK_SECRET)
        signature_header: header received from GitHub (x-hub-signature-256)
    """
    if not signature_header:
        raise ExternalIntegrationException("x-hub-signature-256 header is missing!")
    hash_object = hmac.new(
        secret_token.encode("utf-8"), msg=payload_body, digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, signature_header):
        raise ExternalIntegrationException("Request signatures didn't match!")


@csrf_exempt
@require_POST
def github(request):
    try:
        payload = json.loads(request.body)
        event = request.headers.get("X-GitHub-Event", "ping")
        guid = request.headers.get("X-GitHub-Delivery")
        request_signature = request.headers.get("X-Hub-Signature")
        verify_signature(
            request.body, settings.GITHUB_WEBHOOK_SECRET, request_signature
        )
        if event == "ping":
            return HttpResponse(status=200)
        if event == "installation" or event == "installation_repositories":
            try:
                GithubService.manage_github_repositories(payload)
            except:
                pass
            return HttpResponse(status=200)
        if event not in VALID_EVENTS:
            logger.warning(f"Received invalid github event: {event} - {payload}")
            return HttpResponse(status=200)
        installation_id = payload["installation"]["id"]
        user_integration = IntegrationRepository.get_user_integration(
            {
                "integration__name": "Github",
                "configuration__contains": [installation_id],
            },
        )
        disabled_events = (
            DisabledUserIntegrationEventRepository.get_disabled_user_integration_events(
                user_integration_id=user_integration.id
            )
        )
        if is_event_and_action_disabled(
            disabled_events, event, payload.get("action", None)
        ):
            return HttpResponse(status=200)
        title = f"{' '.join(event.split('_'))} {' '.join(payload.get('action', '').split('_'))}"
        title = title[0].upper() + title[1:]
        payload["event"] = event
        i_am_mentioned = False
        if (
            "comment" in event
            and f"@{user_integration.account_display_name}"
            in payload.get("comment", {}).get("body", "")
        ):
            i_am_mentioned = True
        InboxRepository.add_item(
            {
                "title": title,
                "cause": json.dumps(payload["sender"]),
                "body": json.dumps(payload),
                "is_body_html": False,
                "user_integration_id": user_integration.id,
                "uid": guid,
                "category": "comment" if "comment" in event else "notification",
                "i_am_mentioned": i_am_mentioned,
            }
        )
        return HttpResponse(status=200)
    except ExternalIntegrationException:
        logger.exception(
            f"An error occurred while processing github webhook",
            exc_info=True,
            extra={
                "body": payload,
                "headers": request.headers,
                "event": event,
                "guid": guid,
                "traceback": traceback.format_exc(),
            },
        )
        return HttpResponse(status=403)
    except Exception:
        logger.exception(
            f"An error occurred while processing github webhook",
            exc_info=True,
            extra={
                "body": payload,
                "headers": request.headers,
                "event": event,
                "guid": guid,
                "traceback": traceback.format_exc(),
            },
        )
        return HttpResponse(status=500)
