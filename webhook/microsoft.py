import json
import logging
import traceback
import uuid
from tempfile import NamedTemporaryFile

from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import status

from common.responses import error_response
from document.repository import DocumentRepository
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
        mail_has_attachments = mail.get("hasAttachments", False)
        inbox_uid = f"{mail['id']}-{integration['id']}"
        if mail_has_attachments:
            attachments_response = service.get_attachments(message_id)
            attachments_encoded = attachments_response.get("value", [])
            attachments = []
            for attachment in attachments_encoded:
                content_bytes = attachment.get("contentBytes")
                if isinstance(content_bytes, str):
                    content_bytes = content_bytes.encode("utf-8")
                temp_file = NamedTemporaryFile(delete=True)
                temp_file.write(content_bytes)
                temp_file.flush()
                content_file = ContentFile(content_bytes, name=attachment.get("name"))
                attachments.append(
                    {
                        "name": attachment["name"],
                        "user_id": integration["user_id"],
                        "link": None,
                        "file": content_file,
                        "user_integration_id": integration["id"],
                        "inbox_uid": inbox_uid,
                        "uid": uuid.uuid4().hex,
                    }
                )
                temp_file.close()
        with transaction.atomic():
            InboxRepository.add_items(
                [
                    {
                        "title": mail["subject"],
                        "cause": f"{mail['from']['emailAddress']['name']} <{mail['from']['emailAddress']['address']}>",
                        "body": mail["body"]["content"],
                        "is_body_html": mail["body"]["contentType"] == "html",
                        "user_integration_id": integration["id"],
                        "uid": inbox_uid,
                        "category": "message",
                        "i_am_mentioned": True,
                    }
                ]
            )
            if len(attachments) > 0:
                DocumentRepository.add_documents(attachments)
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
