from inbox.models import GoogleMail
from inbox.repository import InboxRepository


class GoogleMailService:
    @staticmethod
    def create_inbox_item_from_mail(
        sender: GoogleMail, instance: GoogleMail, created: bool, **kwargs
    ):
        InboxRepository.add_item(
            {
                "title": GoogleMailService._get_mail_header(
                    "Subject", instance.payload["headers"]
                ),
                "cause": GoogleMailService._et_mail_header(
                    "From", instance.payload["headers"]
                ),
                "body": GoogleMailService._get_mail_body(instance.payload),
                "is_body_html": GoogleMailService._is_body_html(instance.payload),
                "user_integration_id": instance.user_integration_id,
                "created_at": instance.created_at,
                "uid": f"{instance.message_id}-{instance.user_integration_id}",
            }
        )

    @staticmethod
    def _get_mail_header(field: str, headers: list):
        for header in headers:
            if header["name"] == field:
                return header["value"]
        return None

    @staticmethod
    def _get_mail_body(payload: dict):
        if "parts" not in payload:
            return payload["body"]["data"]
        else:
            return GoogleMailService._get_mail_body(payload["parts"][0])

    @staticmethod
    def _is_body_html(payload: dict):
        if "parts" not in payload:
            return payload["mimeType"] == "text/html"
        else:
            return GoogleMailService._is_body_html(payload["parts"][0])
