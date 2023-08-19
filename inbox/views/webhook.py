import json
import logging
import traceback
from base64 import decodebytes

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from integration.repository import IntegrationRepository

logger = logging.getLogger(__name__)


class WebHookViewSet(ViewSet):
    @action(detail=False, methods=["post"], url_path="google", permission_classes=[])
    def google(self, request):
        try:
            payload = request.data
            encoded_data = payload["message"]["data"]
            decoded_data = json.loads(decodebytes(encoded_data.encode()).decode())
            email = decoded_data["emailAddress"]
            history_id = decoded_data["historyId"]
            integration = IntegrationRepository.get_integration_user(
                filters={
                    "account_id": email,
                    "integration__name": "Gmail",
                }
            )
        except Exception:
            logger.error(
                f"An error occurred processing webhook for google request.\n{traceback.format_exc()}"
            )
            return Response(
                {"detail": "An error occurred. Please try again later!"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
