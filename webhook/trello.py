import base64
import hashlib
import hmac
import json
import logging
import traceback

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from inbox.repository import InboxRepository
from integration.repository import IntegrationRepository
from integration.repository.events import DisabledUserIntegrationEventRepository
from integration.utils.events import is_event_and_action_disabled

logger = logging.getLogger(__name__)

EVENT_MAP = {
    "createBoard": "Created a board",
    "updateBoard": "Updated board details",
    "convertToCardFromCheckItem": "Converted a check item to a card",
    "createCard": "Created a card",
    "deleteCard": "Deleted a card",
    "updateCard": "Updated card details",
    "removeChecklistFromCard": "Removed a checklist from a card",
    "updateCheckItemStateOnCard": "Updated check item state on a card",
    "updateChecklist": "Updated checklist details",
    "updateList": "Updated list details",
    "addLabelToCard": "A label was added to a card",
    "createCheckItem": "Created a check item",
    "deleteCheckItem": "Deleted a check item",
    "removeLabelFromCard": "Removed a label from a card",
    "updateCheckItem": "Updated check item details",
    "addChecklistToCard": "A checklist was added to a card",
    "addMemberToCard": "A member was added to a card",
    "addMemberToBoard": "A member was added to a board",
    "moveCardFromBoard": "Moved a card from one board to another",
    "moveCardToBoard": "Moved a card to a different board",
    "moveListFromBoard": "Moved a list from one board to another",
    "moveListToBoard": "Moved a list to a different board",
    "deleteComment": "Someone deleted their comment on a card",
    "updateComment": "Someone updated their comment on a card",
    "commentCard": "Someone commented on a card",
    # TODO: handle during document module creation
    "deleteAttachmentFromCard": "Deleted an attachment from a card",
    "addAttachmentToCard": "An attachment was added to a card",
}


def base64Digest(secret):
    """
    Returns a base64 encoded string of the hmac digest of the secret.
    """
    secret_bytes = secret.encode() if isinstance(secret, str) else secret
    client_secret_bytes = settings.TRELLO_APP_CLIENT_SECRET.encode()
    mac = hmac.new(client_secret_bytes, secret_bytes, hashlib.sha1)
    return base64.b64encode(mac.digest())


def is_from_trello(header, request_body, user_integration_id):
    """
    Checks if the request is from Trello.
    """
    hashed_header = base64Digest(header)
    hashed_body = base64Digest(
        base64Digest(
            request_body.decode()
            + f"{settings.BACKEND_URL}/webhook/trello/{user_integration_id}"
        )
    )
    return hmac.compare_digest(hashed_header, hashed_body)


@csrf_exempt
@require_http_methods(["POST", "HEAD"])
def trello(request, user_integration_id):
    """
    Trello webhook.
    """
    try:
        headers = request.headers
        if request.method == "HEAD":
            return HttpResponse(status=200)
        if not is_from_trello(
            headers.get("x-trello-webhook", ""), request.body, user_integration_id
        ):
            logger.warning(
                f"Received a request from an unknown source.",
                extra={
                    "body": request.body,
                    "headers": headers,
                },
            )
            return HttpResponse(status=403)
        body = json.loads(request.body.decode())
        action = body["action"]
        if action["type"] not in EVENT_MAP.keys():
            return HttpResponse(status=200)
        disabled_events = (
            DisabledUserIntegrationEventRepository.get_disabled_user_integration_events(
                user_integration_id=user_integration_id
            )
        )
        user_integration = IntegrationRepository.get_user_integration(
            {
                "id": user_integration_id,
                "integration__name": "Trello",
            }
        )
        if not is_event_and_action_disabled(disabled_events, action["type"], None):
            i_am_mentioned = False
            if (
                action["type"] == "commentCard"
                and user_integration.account_display_name in action["data"]["text"]
            ) or (
                action["type"] in ["addMemberToCard", "addMemberToBoard"]
                and user_integration.account_id == action["data"].get("idMember", "")
            ):
                i_am_mentioned = True
            InboxRepository.add_item(
                {
                    "uid": action["id"],
                    "title": EVENT_MAP[action["type"]],
                    "body": json.dumps(action),
                    "cause": json.dumps(body["action"]["memberCreator"]),
                    "user_integration_id": user_integration_id,
                    "category": (
                        "notification" if "comment" not in action["type"] else "comment"
                    ),
                    "i_am_mentioned": i_am_mentioned,
                }
            )
        return HttpResponse(status=200)
    except Exception:
        logger.exception(
            f"An error occurred while processing trello webhook.",
            extra={
                "body": request.body,
                "headers": headers,
                "traceback": traceback.format_exc(),
            },
        )
        return HttpResponse(status=500, content="Internal Server Error")
