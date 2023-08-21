import json
import logging
from base64 import decodebytes

from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet

from common.responses import error_response, success_response
from inbox.repository import GoogleMailRepository
from integration.repository import IntegrationRepository
from integration.services.google import GoogleService

logger = logging.getLogger(__name__)


class WebHookViewSet(ViewSet):
    @action(detail=False, methods=["post"], url_path="google", permission_classes=[])
    def google(self, request):
        try:
            payload = request.data
            encoded_data = payload["message"]["data"]
            decoded_data = json.loads(decodebytes(encoded_data.encode()).decode())
            email = decoded_data["emailAddress"]
            google_integrations = IntegrationRepository.get_user_integrations(
                filters={
                    "account_id": email,
                    "integration__name": "Gmail",
                }
            )
            last_known_message = (
                GoogleMailRepository.filter_google_mail(
                    {"user_integration_id": google_integrations[0]["id"]}
                )
                .order_by("-id")
                .first()
            )
            google_service = GoogleService(
                token=google_integrations[0]["meta_data"]["access_token"],
                refresh_token=google_integrations[0]["meta_data"]["refresh_token"],
            )
            new_messages = google_service.get_latest_unread_primary_inbox(
                last_known_message_id=last_known_message.message_id
                if last_known_message
                else None,
            )
            GoogleMailRepository.create_google_mails(
                google_mails=google_service.get_messages(
                    message_ids=[message["id"] for message in new_messages],
                ),
                user_integration_id=google_integrations[0]["id"],
            )
            return success_response()
        except IntegrityError:
            return error_response(
                logger=logger,
                logger_message="IntegrityError occurred processing webhook for google request.",
                error_message="Known error occurred. Please try again later!",
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="An error occurred processing webhook for google request.",
            )
