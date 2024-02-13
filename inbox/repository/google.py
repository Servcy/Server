import uuid

from inbox.services.google import GoogleMailService

REQUIRED_LABELS = {"UNREAD", "INBOX"}
EXCLUDED_LABELS = {
    "SPAM",
    "TRASH",
}


class GoogleMailRepository:
    @staticmethod
    def _has_valid_labels(mail):
        labels = set(mail["labelIds"])
        return REQUIRED_LABELS.issubset(labels) and not labels.intersection(
            EXCLUDED_LABELS
        )

    @staticmethod
    def create_mails(mails: list, user_integration_id: int) -> tuple[list, list]:
        inbox_items = []
        for mail in mails:
            if not GoogleMailRepository._has_valid_labels(mail):
                continue
            body, attachments = GoogleMailService._get_mail_body(
                mail["payload"], mail["id"]
            )
            inbox_items.append(
                {
                    "title": GoogleMailService._get_mail_header(
                        "Subject", mail["payload"]["headers"]
                    ),
                    "cause": GoogleMailService._get_mail_header(
                        "From", mail["payload"]["headers"]
                    ),
                    "body": body,
                    "is_body_html": True,
                    "user_integration_id": user_integration_id,
                    "uid": f"{mail['id']}-{user_integration_id}-{uuid.uuid4()}",
                    "category": "message",
                    "i_am_mentioned": True,
                }
            )
        return inbox_items, attachments
