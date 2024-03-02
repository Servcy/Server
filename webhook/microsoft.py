import json
import logging
import traceback

from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from common.exceptions import IntegrationAccessRevokedException
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
        client_state = notificaiton["value"][0]["clientState"]
        if client_state is None:
            return HttpResponse(status=200)
        elif client_state != settings.MICROSOFT_APP_CLIENT_SECRET:
            return HttpResponse(status=401)
        account_id = notificaiton["value"][0]["clientState"]
        message_id = notificaiton["value"][0]["resourceData"]["id"]
        user_integration = IntegrationRepository.get_user_integrations(
            {"integration__name": "Outlook", "account_id": account_id},
            first=True,
        )
        if user_integration is None:
            return HttpResponse(status=200)
        service = MicrosoftService(
            refresh_token=user_integration["meta_data"]["token"]["refresh_token"]
        )
        mail = service.get_message(message_id)
        sender_email = (
            user_integration["configuration"] is not None
            and mail["from"]["emailAddress"]["address"]
        )
        if sender_email not in user_integration["configuration"].get(
            "whitelisted_emails", []
        ) and f"*@{sender_email.split('@')[1]}" not in user_integration[
            "configuration"
        ].get(
            "whitelisted_emails", []
        ):
            return HttpResponse(status=200)
        mail_has_attachments = mail.get("hasAttachments", False)
        if mail_has_attachments:
            attachments_response = service.get_attachments(message_id)
            attachments_encoded = attachments_response.get("value", [])
            attachments = []
            for attachment in attachments_encoded:
                content_bytes = attachment.get("contentBytes")
                attachments.append(
                    {
                        "name": attachment["name"],
                        "data": content_bytes,
                    }
                )
        with transaction.atomic():
            InboxRepository.add_item(
                {
                    "title": mail["subject"] or "No Subject",
                    "cause": f"{mail['from']['emailAddress']['name']} <{mail['from']['emailAddress']['address']}>",
                    "body": mail["body"]["content"],
                    "is_body_html": mail["body"]["contentType"] == "html",
                    "user_integration_id": user_integration["id"],
                    "uid": mail["id"],
                    "category": "message",
                    "i_am_mentioned": True,
                    "attachments": attachments if mail_has_attachments else [],
                }
            )
        return HttpResponse(status=200)
    except IntegrityError:
        return HttpResponse(status=200)
    except IntegrationAccessRevokedException:
        if (
            user_integration
            and isinstance(user_integration, dict)
            and user_integration.get("id")
        ):
            IntegrationRepository.revoke_user_integrations(user_integration.get("id"))
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
