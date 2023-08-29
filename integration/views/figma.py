import json
import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action

from common.exceptions import ExternalIntegrationException
from common.responses import error_response, success_response
from integration.repository import IntegrationRepository
from integration.services.figma import FigmaService

logger = logging.getLogger(__name__)


class FigmaViewset(viewsets.ViewSet):
    @action(
        detail=False,
        methods=["PUT"],
        url_path="configure",
    )
    def configure(self, request):
        """
        Configure the Figma integration for a user
        """
        try:
            data = request.data
            team_ids = set(data.get("teamIds", []))
            user_integration_id = int(data.get("userIntegrationId", 0))
            if not user_integration_id or not team_ids:
                return error_response(
                    logger=logger,
                    logger_message="Invalid request data received.",
                    error_message="teamIds and userIntegrationId are required.",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            integration = IntegrationRepository.get_user_integrations(
                filters={
                    "id": user_integration_id,
                    "integration__name": "Figma",
                },
                first=True,
            )
            tokens = json.loads(integration["meta_data"]["token"].replace("'", '"'))
            refresh_token = tokens["refresh_token"]
            service = FigmaService(refresh_token=refresh_token)
            service.create_webhooks(team_ids=team_ids)
            return success_response(status=status.HTTP_200_OK)
        except ExternalIntegrationException as e:
            return error_response(
                logger=logger,
                error_message=e.message,
                logger_message=f"An error occurred while configuring Figma integration. {e.message}",
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="An error occurred while configuring Figma integration.",
            )
