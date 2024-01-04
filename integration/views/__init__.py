import logging

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet, ViewSet, mixins

from common.exceptions import ExternalIntegrationException
from common.responses import error_response, success_response
from integration.models import DisabledUserIntegrationEvent, IntegrationEvent
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
                (
                    configuration["webhook_ids"],
                    configuration["team_ids"],
                ) = service.create_webhooks(
                    team_ids=team_ids, user_integration_id=user_integration_id
                )
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


class IntegrationEventViewSet(ViewSet):
    @action(detail=False, methods=["post"], url_path="disable-event")
    def disable_user_integration_event(self, request):
        try:
            user_id = request.user.id
            integration_id = int(request.data.get("integration_id", 0))
            if not integration_id:
                return error_response(
                    logger=logger,
                    logger_message="Integration id is required",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            event_type = request.data.get("event_type")
            if not event_type:
                return error_response(
                    logger=logger,
                    logger_message="Event type is required",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            integration_event = IntegrationEvent.objects.filter(
                integration_id=integration_id, event_type=event_type
            ).first()
            if not integration_event:
                return error_response(
                    logger=logger,
                    logger_message="Integration event not found",
                    status=status.HTTP_404_NOT_FOUND,
                )
            user_integration = IntegrationRepository.get_user_integrations(
                filters={"user_id": user_id, "integration_id": integration_id},
                first=True,
            )
            if not user_integration:
                return error_response(
                    logger=logger,
                    logger_message="User integration not found",
                    status=status.HTTP_404_NOT_FOUND,
                )
            DisabledUserIntegrationEvent.objects.create(
                user_integration_id=user_integration["id"],
                integration_event_id=integration_event.id,
            )
            return success_response(
                success_message="Integration event disabled successfully",
            )
        except DisabledUserIntegrationEvent.DoesNotExist:
            return error_response(
                logger=logger,
                logger_message="Integration event already disabled",
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="Error while disabling integration event",
            )

    @action(detail=False, methods=["post"], url_path="enable-event")
    def enable_user_integration_event(self, request):
        try:
            user_id = request.user.id
            integration_id = int(request.data.get("integration_id", 0))
            if not integration_id:
                return error_response(
                    logger=logger,
                    logger_message="Integration id is required",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            event_type = request.data.get("event_type")
            if not event_type:
                return error_response(
                    logger=logger,
                    logger_message="Event type is required",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            integration_event = IntegrationEvent.objects.filter(
                integration_id=integration_id, event_type=event_type
            ).first()
            if not integration_event:
                return error_response(
                    logger=logger,
                    logger_message="Integration event not found",
                    status=status.HTTP_404_NOT_FOUND,
                )
            user_integration = IntegrationRepository.get_user_integrations(
                filters={"user_id": user_id, "integration_id": integration_id},
                first=True,
            )
            if not user_integration:
                return error_response(
                    logger=logger,
                    logger_message="User integration not found",
                    status=status.HTTP_404_NOT_FOUND,
                )
            DisabledUserIntegrationEvent.objects.filter(
                user_integration_id=user_integration["id"],
                integration_event_id=integration_event.id,
            ).delete()
            return success_response(
                success_message="Integration event disabled successfully",
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="Error while enabling integration event",
            )

    @action(detail=False, methods=["get"], url_path="fetch-events")
    def fetch_integration_events(self, request):
        try:
            integration_id = int(request.GET.get("integration_id", 0))
            if not integration_id:
                return error_response(
                    logger=logger,
                    logger_message="Integration id is required",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            integration_events = IntegrationEvent.objects.filter(
                integration_id=integration_id
            ).all()
            disabled_user_integration_events = (
                DisabledUserIntegrationEvent.objects.filter(
                    user_integration__integration_id=integration_id
                ).values_list("integration_event_id", flat=True)
            )
            integration_events = [
                {
                    "id": integration_event.id,
                    "event_type": integration_event.event_type,
                    "is_disabled": integration_event.id
                    in disabled_user_integration_events,
                }
                for integration_event in integration_events
            ]
            return success_response(
                success_message="Integration events fetched successfully",
                results=integration_events,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="Error while fetching integration events",
            )
