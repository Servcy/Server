import json
import logging
from base64 import decodebytes

from django.db import IntegrityError, transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import status

from common.responses import error_response, success_response
from inbox.repository import InboxRepository
from inbox.repository.google import GoogleMailRepository
from integration.repository import IntegrationRepository
from integration.services.google import GoogleService

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def google(request):
    try:
        payload = request.data
        encoded_data = payload["message"]["data"]
        decoded_data = json.loads(decodebytes(encoded_data.encode()).decode())
        email = decoded_data["emailAddress"]
        integrations = IntegrationRepository.get_user_integrations(
            filters={
                "account_id": email,
                "integration__name": "Gmail",
            },
            first=True,
        )
        if integrations is None:
            logger.error(f"No integration found for email: {email}. Payload: {payload}")
            return error_response(
                logger=logger,
                logger_message="No integration found for email.",
                status=status.HTTP_404_NOT_FOUND,
            )
        last_known_message = (
            GoogleMailRepository.get_mails({"user_integration_id": integrations["id"]})
            .order_by("-id")
            .first()
        )
        service = GoogleService(
            token=integrations["meta_data"]["access_token"],
            refresh_token=integrations["meta_data"]["refresh_token"],
        )
        new_messages = service.get_latest_unread_primary_inbox(
            last_known_message_id=last_known_message.message_id
            if last_known_message
            else None,
        )
        with transaction.atomic():
            inbox_items = GoogleMailRepository.create_mails(
                mails=service.get_messages(
                    message_ids=[message["id"] for message in new_messages],
                ),
                user_integration_id=integrations["id"],
            )
            InboxRepository.add_items(inbox_items)
        return success_response()
    except IntegrityError:
        return success_response()
    except Exception:
        return error_response(
            logger=logger,
            logger_message="An error occurred processing webhook for google request.",
        )
