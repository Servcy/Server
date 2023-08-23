import logging
import traceback

from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from inbox.repository import InboxRepository
from inbox.repository.microsoft import OutlookMailRepository
from integration.repository import IntegrationRepository
from integration.services.microsoft import MicrosoftService

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def microsoft(request):
    validation_token = request.GET.get("validationToken", "")
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
        return HttpResponse(
            content=validation_token, content_type="text/plain", status=200
        )
    except KeyError:
        return HttpResponse(
            content=validation_token, content_type="text/plain", status=200
        )
    except Exception:
        logger.error(
            f"An error occurred while processing notification.\n{traceback.format_exc()}"
        )
        return HttpResponse(status=500)
