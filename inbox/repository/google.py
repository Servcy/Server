from inbox.repository import InboxRepository
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
    def create_mails(
        mails: list,
        user_integration_id: int,
        user_integration_configuration: dict,
    ) -> tuple[list, list, bool]:
        inbox_items = []
        attachments = {}
        has_attachments = False
        for mail in mails:
            sender = GoogleMailService._get_mail_header(
                "From", mail["payload"]["headers"]
            )
            if not sender:
                continue
            sender_email = sender.split("<")[-1].split(">")[0]
            if not GoogleMailRepository._has_valid_labels(mail):
                continue
            if (
                user_integration_configuration is not None
                and sender_email
                not in user_integration_configuration.get("whitelisted_emails", [])
            ):
                continue
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
                    "uid": mail["id"],
                    "category": "message",
                    "i_am_mentioned": True,
                }
            )
            attachments[mail["id"]] = files
            has_attachments = has_attachments or bool(files)
        return inbox_items, attachments, has_attachments
