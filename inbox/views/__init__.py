import logging
import traceback

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from integration.repository import IntegrationRepository
from integration.services.google import GoogleService

logger = logging.getLogger(__name__)


class InboxViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="sync")
    def sync_inbox(self, request):
        try:
            user_id = request.user.id
            google_integrations = IntegrationRepository.get_integration_user(
                filters={
                    "user_id": user_id,
                    "integration__name": "Gmail",
                }
            )
            for google_integration in google_integrations:
                messages = GoogleService.get_latest_unread_primary_inbox(
                    tokens=google_integration["meta_data"],
                    last_message_id="18a0cdff25c33368",
                )
                for message in messages:
                    message_id = message["id"]
                    thread_id = message["threadId"]
                    message = GoogleService.get_message(
                        message_id=message_id,
                        tokens=google_integration["meta_data"],
                    )
                    for header in message["payload"]["headers"]:
                        if header["name"] == "From":
                            print(header["value"], "from")
                        if header["name"] == "Subject":
                            print(header["value"], "subject")
        except Exception:
            logger.error(
                f"An error occurred while inbox sync.\n{traceback.format_exc()}"
            )
            return Response(
                {"detail": "An error occurred. Please try again later!"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
