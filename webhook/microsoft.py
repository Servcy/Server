import json
import logging
import traceback

from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import status

from common.responses import error_response
from inbox.repository import InboxRepository
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
            logger.warning(f"No integration found for outlook: {account_id}")
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
            InboxRepository.add_items(
                [
                    {
                        "title": mail["subject"],
                        "cause": f"{mail['from']['emailAddress']['name']} <{mail['from']['emailAddress']['address']}>",
                        "body": mail["body"]["content"],
                        "is_body_html": mail["body"]["contentType"] == "html",
                        "user_integration_id": integration["id"],
                        "uid": f"{mail['id']}-{integration['id']}",
                        "category": "message",
                    }
                ]
            )
        return HttpResponse(status=200)
    except IntegrityError:
        return HttpResponse(status=200)
    except KeyError:
        logger.exception(
            f"A key error occurred while processing microsoft notification {notificaiton}.",
            extra={
                "traceback": traceback.format_exc(),
            },
        )
        return HttpResponse(status=200)
    except Exception:
        logger.exception(
            f"An error occurred while processing notification.",
            exc_info=True,
            extra={
                "notificaiton": notificaiton,
                "headers": request.headers,
                "traceback": traceback.format_exc(),
            },
        )
        return HttpResponse(status=500)
