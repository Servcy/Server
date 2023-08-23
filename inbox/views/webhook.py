import json
import logging
import traceback
from base64 import decodebytes

from django.db import IntegrityError, transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from common.responses import error_response, success_response
from inbox.repository import InboxRepository
from inbox.repository.google import GoogleMailRepository
from inbox.repository.microsoft import OutlookMailRepository
from integration.repository import IntegrationRepository
from integration.services.google import GoogleService
from integration.services.microsoft import MicrosoftService

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class WebHookViewSet(ViewSet):
    @action(detail=False, methods=["post"], url_path="google", permission_classes=[])
    def google(self, request):
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
                logger.error(
                    f"No integration found for email: {email}. Payload: {payload}"
                )
                return error_response(
                    logger=logger,
                    logger_message="No integration found for email.",
                    status=status.HTTP_404_NOT_FOUND,
                )
            last_known_message = (
                GoogleMailRepository.get_mails(
                    {"user_integration_id": integrations["id"]}
                )
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

    @action(detail=False, methods=["post"], url_path="microsoft", permission_classes=[])
    def microsoft(self, request):
        validation_token = request.GET.get("validationToken", None)
        try:
            notificaiton = request.data
            account_id = int(notificaiton["value"][0]["clientState"])
            message_id = notificaiton["value"][0]["resourceData"]["id"]
            user_integration = IntegrationRepository.get_user_integrations(
                {"integration__name": "Outlook", "account_id": account_id}
            )
            service = MicrosoftService(
                refresh_token=user_integration["meta_data"]["token"]["refresh_token"]
            )
            mail = service.get_message(message_id)
            with transaction.atomic():
                inbox_items = OutlookMailRepository.create_mail(
                    mail=mail,
                    user_integration_id=user_integration["id"],
                )
                InboxRepository.add_items(inbox_items)
            return Response(validation_token, content_type="text/plain", status=200)
        except KeyError:
            return Response(
                validation_token,
                content_type="text/plain",
                status=200,
            )
        except Exception:
            logger.error(
                f"An error occurred while processing notification.\n{traceback.format_exc()}"
            )
            return Response(status=500)
