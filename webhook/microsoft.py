import json
import logging

from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import status

from common.responses import error_response
from inbox.repository import InboxRepository
from inbox.repository.microsoft import OutlookMailRepository
from integration.repository import IntegrationRepository
from integration.services.microsoft import MicrosoftService

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def microsoft(request):
    try:
        validation_token = request.GET.get("validationToken", "")
        if validation_token:
            return HttpResponse(
                content=validation_token, content_type="text/plain", status=200
            )
        notificaiton = json.loads(request.body.decode("utf-8"))
        account_id = notificaiton["value"][0]["clientState"]
        message_id = notificaiton["value"][0]["resourceData"]["id"]
        integration = IntegrationRepository.get_user_integrations(
            {"integration__name": "Outlook", "account_id": account_id},
            first=True,
        )
        if integration is None:
            logger.exception(f"No integration found for outlook: {account_id}")
            return error_response(
                logger=logger,
                logger_message="No integration found for email.",
                status=status.HTTP_404_NOT_FOUND,
            )
        service = MicrosoftService(
            refresh_token=integration["meta_data"]["token"]["refresh_token"]
        )
        mail = service.get_message(message_id)
        with transaction.atomic():
            inbox_item = OutlookMailRepository.create_mail(
                mail=mail,
                user_integration_id=integration["id"],
            )
            InboxRepository.add_items([inbox_item])
        return HttpResponse(status=200)
    except IntegrityError:
        return HttpResponse(status=200)
    except KeyError:
        logger.exception(
            f"A key error occurred while processing microsoft notification {notificaiton}.",
            exc_info=True,
        )
        return HttpResponse(status=200)
    except Exception as err:
        logger.exception(
            f"An error occurred while processing notification.",
            exc_info=True,
            extra={"body": request.body, "headers": request.headers},
        )
        return HttpResponse(status=500)
