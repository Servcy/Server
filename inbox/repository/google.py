import datetime

from django.db import transaction
from django.utils import timezone

from inbox.models import GoogleMail


class GoogleMailRepository:
    @staticmethod
    def get_google_mail(filters={}):
        return GoogleMail.objects.get(**filters)

    @staticmethod
    def filter_google_mail(filters={}):
        return GoogleMail.objects.filter(**filters)

    @staticmethod
    def create_google_mails(
        google_mails: list, user_integration_id: int, batch_size: int = 100
    ):
        google_mail_objects = []
        for google_mail in google_mails:
            google_mail_objects.append(
                GoogleMail(
                    thread_id=google_mail["threadId"],
                    history_id=google_mail["historyId"],
                    message_id=google_mail["id"],
                    snippet=google_mail["snippet"],
                    size_estimate=google_mail["sizeEstimate"],
                    label_ids=google_mail["labelIds"],
                    payload=google_mail["payload"],
                    internal_date=timezone.make_aware(
                        datetime.datetime.fromtimestamp(
                            int(google_mail["internalDate"]) / 1000
                        )
                    ),
                    user_integration_id=user_integration_id,
                )
            )
        GoogleMail.objects.bulk_create(google_mail_objects, batch_size=batch_size)

    @staticmethod
    def read_google_mails(filters: dict = {}, values: list = ["id"]) -> list[dict]:
        """
        Read google mails from the database and update the is_read flag.
        """
        mails = []
        with transaction.atomic():
            mails = GoogleMail.objects.filter(**filters).values(*values)
            GoogleMail.objects.filter(id__in=[mail["id"] for mail in mails]).update(
                is_read=True
            )
        return mails
