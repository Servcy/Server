import json
import logging
from base64 import decodebytes

from django.db import IntegrityError, transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import status

from common.responses import error_response, success_response
from inbox.repository import InboxRepository
from inbox.repository.google import GoogleMailRepository
from inbox.services.google import GoogleMailService
from integration.repository import IntegrationRepository
from integration.services.google import GoogleService

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def google(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
        encoded_data = payload["message"]["data"]
        decoded_data = json.loads(decodebytes(encoded_data.encode()).decode())
        email = decoded_data["emailAddress"]
        integration = IntegrationRepository.get_user_integrations(
            filters={
                "account_id": email,
                "integration__name": "Gmail",
            },
            first=True,
        )
        if integration is None:
            logger.error(f"No integration found for email: {email}. Payload: {payload}")
            return error_response(
                logger=logger,
                logger_message="No integration found for email.",
                status=status.HTTP_404_NOT_FOUND,
            )
        last_known_message = (
            GoogleMailRepository.get_mails({"user_integration_id": integration["id"]})
            .order_by("-id")
            .first()
        )
        service = GoogleService(
            token=integration["meta_data"]["access_token"],
            refresh_token=integration["meta_data"]["refresh_token"],
        )
        new_messages = service.get_latest_unread_primary_inbox(
            last_known_message_id=last_known_message.message_id
            if last_known_message
            else None,
        )
        inbox_items = []
        mail_objects = GoogleMailRepository.create_mails(
            mails=service.get_messages(
                message_ids=[message["id"] for message in new_messages],
            ),
            user_integration_id=integration["id"],
        )
        with transaction.atomic():
            for mail in mail_objects:
                try:
                    mail.save()
                    inbox_items.append(
                        {
                            "title": GoogleMailService._get_mail_header(
                                "Subject", mail["payload"]["headers"]
                            ),
                            "cause": GoogleMailService._get_mail_header(
                                "From", mail["payload"]["headers"]
                            ),
                            "body": GoogleMailService._get_mail_body(mail["payload"]),
                            "is_body_html": GoogleMailService._is_body_html(
                                mail["payload"]
                            ),
                            "user_integration_id": integration["id"],
                            "uid": f"{mail['id']}-{integration['id']}",
                        }
                    )
                except IntegrityError:
                    pass
            InboxRepository.add_items(inbox_items)
        return success_response()
    except Exception:
        return error_response(
            logger=logger,
            logger_message="An error occurred processing webhook for google request.",
        )
