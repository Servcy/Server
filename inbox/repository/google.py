import uuid

from inbox.services.google import GoogleMailService
from inbox.repository import InboxRepository

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
    def create_mails(
        mails: list, user_integration_id: int, user_id: int
    ) -> tuple[list, list, bool]:
        inbox_items = []
        attachments = {}
        has_attachments = False
        for mail in mails:
            if not GoogleMailRepository._has_valid_labels(mail):
                continue
            sender = GoogleMailService._get_mail_header(
                "From", mail["payload"]["headers"]
            )
            try:
                sender_email = sender.split("<")[-1].split(">")[0]
                if InboxRepository.is_email_blocked(sender_email, user_id):
                    continue
            except:
                pass
            uid = f"{mail['id']}-{user_integration_id}-{uuid.uuid4()}"
            body, files = GoogleMailService._get_mail_body(mail["payload"], mail["id"])
            inbox_items.append(
                {
                    "title": GoogleMailService._get_mail_header(
                        "Subject", mail["payload"]["headers"]
                    )
                    or "No Subject",
                    "cause": sender,
                    "body": body,
                    "is_body_html": True,
                    "user_integration_id": user_integration_id,
                    "uid": uid,
                    "category": "message",
                    "i_am_mentioned": True,
                }
            )
            attachments[uid] = files
            has_attachments = has_attachments or bool(files)
        return inbox_items, attachments, has_attachments
