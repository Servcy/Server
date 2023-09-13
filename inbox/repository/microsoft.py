from inbox.models import OutlookMail


class OutlookMailRepository:
    """
    Repository for Outlook Mail
    """

    @staticmethod
    def create_mail(mail: dict, user_integration_id: int) -> OutlookMail:
        """
        Create Outlook Mail
        """
        OutlookMail.objects.create(
            message_id=mail["id"],
            categories=mail["categories"],
            payload=mail,
            user_integration_id=user_integration_id,
        )
        return {
            "title": mail["subject"],
            "cause": f"{mail['from']['emailAddress']['name']} <{mail['from']['emailAddress']['address']}>",
            "body": mail["body"]["content"],
            "is_body_html": mail["body"]["contentType"] == "html",
            "user_integration_id": user_integration_id,
            "uid": f"{mail['id']}-{user_integration_id}",
            "category": "message",
        }
