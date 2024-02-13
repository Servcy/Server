import json
import logging
import traceback
from base64 import decodebytes
from tempfile import NamedTemporaryFile

from django.core.files.base import ContentFile
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from common.exceptions import IntegrationAccessRevokedException
from document.repository.document import DocumentRepository
from inbox.repository import InboxRepository
from inbox.repository.google import GoogleMailRepository
from integration.repository import IntegrationRepository
from integration.services.google import GoogleService

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def google(request):
    email = None
    history_id = None
    try:
        payload = json.loads(request.body.decode("utf-8"))
        encoded_data = payload["message"]["data"]
        decoded_data = json.loads(decodebytes(encoded_data.encode()).decode())
        email = decoded_data["emailAddress"]
        history_id = decoded_data["historyId"]
        integration = IntegrationRepository.get_user_integrations(
            filters={
                "account_id": email,
                "integration__name": "Gmail",
            },
            first=True,
        )
        if integration is None:
            GoogleService.remove_publisher_for_user(email=email)
            return HttpResponse(status=200)
        IntegrationRepository.update_integraion_meta_data(
            user_integration_id=integration["id"],
            meta_data={
                **integration["meta_data"],
                "last_history_id": history_id,
            },
        )
        last_history_id = int(integration["meta_data"].get("last_history_id", 0))
        if last_history_id == 0:
            return HttpResponse(status=200)
        service = GoogleService(
            access_token=integration["meta_data"]["token"]["access_token"],
            refresh_token=integration["meta_data"]["token"]["refresh_token"],
        )
        message_ids = service.get_latest_unread_primary_inbox(last_history_id)
        if not message_ids:
            return HttpResponse(status=200)
        mails = service.get_messages(
            message_ids=message_ids,
        )
        inbox_items, attachments = GoogleMailRepository.create_mails(
            mails=mails,
            user_integration_id=integration["id"],
        )
        documents = []
        if len(attachments) > 0:
            attachments = service.get_attachments(attachments=attachments)
        for attachment in attachments:
            content_bytes = attachment.get("data")
            if isinstance(content_bytes, str):
                content_bytes = content_bytes.encode("utf-8")
            temp_file = NamedTemporaryFile(delete=True)
            temp_file.write(content_bytes)
            temp_file.flush()
            content_file = ContentFile(content_bytes, name=attachment.get("filename"))
            documents.append(
                {
                    "name": attachment["filename"],
                    "user_id": integration["user_id"],
                    "link": None,
                    "file": content_file,
                    "user_integration_id": integration["id"],
                }
            )
            temp_file.close()
        with transaction.atomic():
            DocumentRepository.add_documents(documents)
            InboxRepository.add_items(inbox_items)
        return HttpResponse(status=200)
    except IntegrationAccessRevokedException:
        IntegrationRepository.revoke_user_integrations(integration.get("id", 0))
        return HttpResponse(status=200)
    except Exception:
        logger.exception(
            f"An error occurred processing webhook for google request. {email} {history_id}",
            extra={
                "payload": payload,
                "headers": request.headers,
                "traceback": traceback.format_exc(),
            },
        )
        return HttpResponse(status=500)
