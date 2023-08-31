import json
import logging
from base64 import decodebytes

from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import status

from common.responses import error_response
from inbox.repository import InboxRepository
from inbox.repository.google import GoogleMailRepository
from integration.repository import IntegrationRepository
from integration.services.google import GoogleService

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def google(request):
    email = None
    history_id = None
    try:
        payload = json.loads(request.body.decode("utf-8"))
        encoded_data = payload["message"]["data"]
        decoded_data = json.loads(decodebytes(encoded_data.encode()).decode())
        email = decoded_data["emailAddress"]
        history_id = decoded_data["historyId"]
        integration = IntegrationRepository.get_user_integrations(
            filters={
                "account_id": email,
                "integration__name": "Gmail",
            },
            first=True,
        )
        if integration is None:
            logger.error(f"No integration found for email: {email}. Payload: {payload}")
            return error_response(
                logger=logger,
                logger_message="No integration found for email.",
                status=status.HTTP_404_NOT_FOUND,
            )
        last_history_id = int(integration["meta_data"]["last_history_id"])
        IntegrationRepository.update_integraion_meta_data(
            user_integration_id=integration["id"],
            meta_data={
                **integration["meta_data"],
                "last_history_id": history_id,
            },
        )
        service = GoogleService(
            token=integration["meta_data"]["token"]["access_token"],
            refresh_token=integration["meta_data"]["token"]["refresh_token"],
        )
        message_ids = service.get_latest_unread_primary_inbox(last_history_id)
        if not message_ids:
            return HttpResponse(
                status=status.HTTP_200_OK, content="success", content_type="text/plain"
            )
        with transaction.atomic():
            inbox_items = GoogleMailRepository.create_mails(
                mails=service.get_messages(
                    message_ids=message_ids,
                ),
                user_integration_id=integration["id"],
            )
            InboxRepository.add_items(inbox_items)
        return HttpResponse(
            status=status.HTTP_200_OK, content="success", content_type="text/plain"
        )
    except Exception:
        return error_response(
            logger=logger,
            logger_message=f"An error occurred processing webhook for google request. {email} {history_id}",
        )
