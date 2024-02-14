import datetime

from django.db.models import Q

from inbox.models import Inbox, BlockedEmail


class InboxRepository:
    """
    Inbox Repository
    """

    @staticmethod
    def block_email(email: str, user):
        """
        Block an email.
        """
        return BlockedEmail.objects.create(email=email, user=user)

    @staticmethod
    def is_email_blocked(email: str, user_id) -> bool:
        """
        Check if an email is blocked.
        """
        return BlockedEmail.objects.filter(email=email, user_id=user_id).exists()

    @staticmethod
    def add_item(item: dict) -> Inbox:
        """
        Add an item to the inbox.
        """
        return Inbox.objects.create(**item)

    def add_items(items: list[dict]) -> list[Inbox]:
        """
        Add items to the inbox.
        """
        return Inbox.objects.bulk_create([Inbox(**item) for item in items])

    @staticmethod
    def archive_item(item_ids: list[int]) -> Inbox:
        """
        Archive an item in the inbox.
        """
        return Inbox.objects.filter(id__in=item_ids).update(
            is_archived=True, updated_at=datetime.datetime.now()
        )

    @staticmethod
    def read_item(item_id: int) -> Inbox:
        """
        Archive an item in the inbox.
        """
        return Inbox.objects.filter(id=item_id).update(
            is_read=True, updated_at=datetime.datetime.now()
        )

    @staticmethod
    def delete_items(item_ids: list[int]) -> None:
        """
        Archive an item in the inbox.
        """
        return Inbox.objects.filter(id__in=item_ids).delete()

    @staticmethod
    def filter(query: Q) -> list[Inbox]:
        """
        Filter inbox items.
        """
        return Inbox.objects.filter(query)
