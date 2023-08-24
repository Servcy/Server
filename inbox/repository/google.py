import datetime

from django.utils import timezone

from inbox.models import GoogleMail


class GoogleMailRepository:
    @staticmethod
    def get_mails(filters={}):
        return GoogleMail.objects.filter(**filters)

    @staticmethod
    def create_mails(mails: list, user_integration_id: int) -> list[dict]:
        mail_objects = []
        for mail in mails:
            mail_objects.append(
                GoogleMail(
                    thread_id=mail["threadId"],
                    history_id=mail["historyId"],
                    message_id=mail["id"],
                    snippet=mail["snippet"],
                    size_estimate=mail["sizeEstimate"],
                    label_ids=mail["labelIds"],
                    payload=mail["payload"],
                    internal_date=timezone.make_aware(
                        datetime.datetime.fromtimestamp(
                            int(mail["internalDate"]) / 1000
                        )
                    ),
                    user_integration_id=user_integration_id,
                )
            )
        return mail_objects
