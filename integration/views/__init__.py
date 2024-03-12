import json
import logging

from rest_framework import status
from rest_framework.decorators import action

from common.exceptions import ExternalIntegrationException
from common.responses import error_response, success_response
from common.views import BaseViewSet
from integration.models import UserIntegration
from integration.repository import IntegrationRepository
from integration.repository.events import (
    DisabledUserIntegrationEventRepository,
    IntegrationEventRepository,
)
from integration.serializers import UserIntegrationSerializer
from integration.services.figma import FigmaService
from integration.utils.events import determine_integration_event

logger = logging.getLogger(__name__)


class IntegrationViewSet(BaseViewSet):
    @action(detail=False, methods=["get"], url_path="fetch-integrations")
    def fetch_integrations(self, request):
        try:
            requesting_user = request.user
            user_integrations = IntegrationRepository.get_user_integrations(
                {
                    "user_id": requesting_user.id,
                },
                first=False,
                values={
                    "id",
                    "integration_id",
                },
                decrypt_meta_data=False,
            )
            connected_integrations = set()
            for user_integration in user_integrations:
                connected_integrations.add(user_integration["integration_id"])
            integrations = IntegrationRepository.fetch_all_integrations().values(
                "id", "name", "description", "logo", "configure_at"
            )
            integrations = [
                {
                    **integration,
                    "is_connected": integration["id"] in connected_integrations,
                }
                for integration in integrations
            ]
            return success_response(
                success_message="Integrations fetched successfully",
                results=integrations,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="Error while fetching integrations",
            )


class UserIntegrationViewSet(BaseViewSet):
    model = UserIntegration
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
        except ExternalIntegrationException:
            return error_response(
                logger=logger,
                logger_message=f"External error occurred while configuring Figma integration.",
                status=status.HTTP_400_BAD_REQUEST,
                error_message="External error occurred while configuring Figma integration.",
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="An error occurred while configuring Figma integration.",
            )


class IntegrationEventViewSet(BaseViewSet):
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
            event_id = int(request.data.get("event_id", 0))
            if not event_id:
                return error_response(
                    logger=logger,
                    logger_message="Event id is required",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            integration_event = IntegrationEventRepository.filter(
                id=event_id, integration_id=integration_id
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
            DisabledUserIntegrationEventRepository.get_or_create(
                user_integration_id=user_integration["id"],
                integration_event_id=integration_event.id,
                defaults={
                    "actions": request.data.get("actions", []),
                },
            )
            return success_response(
                success_message="Integration event disabled successfully",
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
            event_id = int(request.data.get("event_id", 0))
            if not event_id:
                return error_response(
                    logger=logger,
                    logger_message="Event id is required",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            integration_event = IntegrationEventRepository.filter(
                integration_id=integration_id, id=event_id
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
            DisabledUserIntegrationEventRepository.filter(
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
            integration_events = IntegrationEventRepository.filter(
                integration_id=integration_id
            ).all()
            disabled_user_integration_events = (
                DisabledUserIntegrationEventRepository.filter(
                    user_integration__integration_id=integration_id
                ).values_list("integration_event_id", flat=True)
            )
            integration_events = [
                {
                    "id": integration_event.id,
                    "description": integration_event.description,
                    "name": integration_event.name,
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

    @action(detail=False, methods=["post"], url_path="disable-such-notifications")
    def disable_such_notifications(self, request):
        try:
            user_id = request.user.id
            user_integration_id = int(request.data.get("user_integration_id", 0))
            event = json.loads(request.data.get("event", "{}"))
            if not user_integration_id or not event:
                return error_response(
                    logger=logger,
                    logger_message="User integration id and event are required fields",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user_integration = IntegrationRepository.get_user_integrations(
                filters={
                    "user_id": user_id,
                    "id": user_integration_id,
                },
                first=True,
            )
            if not user_integration:
                return error_response(
                    logger=logger,
                    logger_message="User integration not found",
                    status=status.HTTP_404_NOT_FOUND,
                )
            event_name, action = determine_integration_event(
                user_integration,
                event,
            )
            integration_event = IntegrationEventRepository.filter(
                name=event_name,
                integration_id=user_integration["integration_id"],
            ).first()
            if not integration_event:
                return error_response(
                    logger=logger,
                    logger_message="Integration event not found",
                    status=status.HTTP_404_NOT_FOUND,
                )
            disabled_user_integration_event = (
                DisabledUserIntegrationEventRepository.filter(
                    user_integration_id=user_integration["id"],
                    integration_event_id=integration_event.id,
                ).first()
            )
            if not disabled_user_integration_event:
                DisabledUserIntegrationEventRepository.create(
                    user_integration_id=user_integration["id"],
                    integration_event_id=integration_event.id,
                    actions=[action],
                )
            elif action not in disabled_user_integration_event.actions:
                disabled_user_integration_event.actions.append(action)
                disabled_user_integration_event.save()
            return success_response(
                success_message="Integration event disabled successfully",
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="Error while disabling integration event",
            )
