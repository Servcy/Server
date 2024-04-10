from inbox.services.google import GoogleMailService


class GoogleMailRepository:
    @staticmethod
    def _has_valid_labels(mail):
        labels = set(mail["labelIds"])
        return not labels.intersection(
            {
                "SPAM",
                "TRASH",
            }
        )

    @staticmethod
    def is_email_white_listed(email: str, whitelisted_emails: list) -> bool:
        if email in whitelisted_emails:
            return True
        elif f"*@{email.split('@')[1]}" in whitelisted_emails:
            # for wildcard emails e.g. *@domain.com
            return True
        elif "*@*" in whitelisted_emails:
            # for all emails
            return True
        return False

    @staticmethod
    def create_mails(
        mails: list,
        user_integration_id: int,
        user_integration_configuration: dict,
    ) -> tuple[list, list, bool]:
        inbox_items = []
        attachments = {}
        has_attachments = False
        if user_integration_configuration is None:
            return [], [], False
        for mail in mails:
            sender = GoogleMailService.get_mail_header(
                "From", mail["payload"]["headers"]
            )
            if not sender:
                continue
            sender_email = sender.split("<")[-1].split(">")[0]
            if not GoogleMailRepository._has_valid_labels(
                mail
            ) or not GoogleMailRepository.is_email_white_listed(
                sender_email,
                user_integration_configuration.get("whitelisted_emails", []),
            ):
                continue
            body, files = GoogleMailService.get_mail_body(mail["payload"], mail["id"])
            inbox_items.append(
                {
                    "title": GoogleMailService.get_mail_header(
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
