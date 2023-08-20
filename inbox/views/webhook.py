import json
import logging
import traceback
from base64 import decodebytes

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

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
            google_integrations = IntegrationRepository.get_integration_users(
                filters={
                    "account_id": email,
                    "integration__name": "Gmail",
                }
            )
            last_known_message = (
                GoogleMailRepository.filter_google_mail(
                    {"integration_user_id": google_integrations[0]["id"]}
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
            new_messages_with_data = google_service.get_messages_with_data(
                message_ids=[message["id"] for message in new_messages],
            )
            GoogleMailRepository.create_google_mails(
                google_mails=new_messages_with_data,
                integration_user_id=google_integrations[0]["id"],
            )
            return Response({"detail": "success"}, status=status.HTTP_200_OK)
        except Exception:
            logger.error(
                f"An error occurred processing webhook for google request.\n{traceback.format_exc()}"
            )
            return Response(
                {"detail": "An error occurred. Please try again later!"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
