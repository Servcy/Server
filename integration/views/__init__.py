import json
import logging

from rest_framework import status
from rest_framework.viewsets import GenericViewSet, mixins

from common.exceptions import ExternalIntegrationException
from common.responses import error_response
from integration.repository import IntegrationRepository
from integration.serializers import IntegrationSerializer, UserIntegrationSerializer
from integration.services.figma import FigmaService

logger = logging.getLogger(__name__)


class IntegrationViewSet(
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class = IntegrationSerializer
    queryset = IntegrationSerializer.Meta.model.objects.all()
    ordering_fields = ["name"]

    def get_queryset(self):
        return super().get_queryset().prefetch_related("user_integrations")


class UserIntegrationViewSet(
    mixins.ListModelMixin,
    GenericViewSet,
    mixins.UpdateModelMixin,
):
    serializer_class = UserIntegrationSerializer
    queryset = UserIntegrationSerializer.Meta.model.objects.filter(
        is_revoked=False
    ).all()

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                user_id=self.request.user.id,
                integration__name=self.request.GET.get("integration_name"),
            )
        )

    def partial_update(self, request, *args, **kwargs):
        """
        Used for integration configuration
        """
        try:
            integration_name = request.GET.get("integration_name")
            if integration_name == "Figma":
                user_integration_id = kwargs.get("pk")
                data = request.data
                configuration = data["configuration"]
                team_ids = configuration.get("team_ids")
                user_integration = IntegrationRepository.get_user_integrations(
                    filters={
                        "id": user_integration_id,
                        "integration__name": "Figma",
                    },
                    first=True,
                )
                refresh_token = user_integration["meta_data"]["token"]["refresh_token"]
                service = FigmaService(refresh_token=refresh_token)
                configuration["team_ids"] = service.create_webhooks(team_ids=team_ids)
                request.data["configuration"] = configuration
            return super().partial_update(request, *args, **kwargs)
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
