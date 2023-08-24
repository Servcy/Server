import datetime

from django.db import IntegrityError
from django.utils import timezone

from inbox.models import GoogleMail
from inbox.services.google import GoogleMailService


class GoogleMailRepository:
    @staticmethod
    def get_mails(filters={}):
        return GoogleMail.objects.filter(**filters)

    @staticmethod
    def create_mails(mails: list, user_integration_id: int) -> list[dict]:
        inbox_items = []
        for mail in mails:
            mail_object = GoogleMail(
                thread_id=mail["threadId"],
                history_id=mail["historyId"],
                message_id=mail["id"],
                snippet=mail["snippet"],
                size_estimate=mail["sizeEstimate"],
                label_ids=mail["labelIds"],
                payload=mail["payload"],
                internal_date=timezone.make_aware(
                    datetime.datetime.fromtimestamp(int(mail["internalDate"]) / 1000)
                ),
                user_integration_id=user_integration_id,
            )
            try:
                mail_object.save()
            except IntegrityError:
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
                }
            )
        return inbox_items
