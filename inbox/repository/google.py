from inbox.services.google import GoogleMailService

REQUIRED_LABELS = {"UNREAD", "CATEGORY_PERSONAL", "INBOX"}
EXCLUDED_LABELS = {
    "SPAM",
    "CATEGORY_SOCIAL",
    "CATEGORY_PROMOTIONS",
    "CATEGORY_UPDATES",
    "CATEGORY_FORUMS",
    "PROMOTIONS",
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
    def create_mails(mails: list, user_integration_id: int) -> list[dict]:
        inbox_items = []
        for mail in mails:
            if not GoogleMailRepository._has_valid_labels(mail):
                continue
            inbox_items.append(
                {
                    "title": GoogleMailService._get_mail_header(
                        "Subject", mail["payload"]["headers"]
                    ),
                    "cause": GoogleMailService._get_mail_header(
                        "From", mail["payload"]["headers"]
                    ),
                    "body": GoogleMailService._get_mail_body(mail["payload"]),
                    "is_body_html": GoogleMailService._is_body_html(mail["payload"]),
                    "user_integration_id": user_integration_id,
                    "uid": f"{mail['id']}-{user_integration_id}",
                    "category": "message",
                }
            )
        return inbox_items
