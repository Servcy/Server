from django.db.models import Q
from django.utils import timezone

from inbox.models import Inbox


class InboxRepository:
    """
    Inbox Repository
    """

    @staticmethod
    def filter(query: Q) -> list[Inbox]:
        """
        Filter inbox items.
        """
        return Inbox.objects.filter(query)

    @staticmethod
    def add_item(item: dict) -> None:
        """
        Add an item to the inbox.
        """
        Inbox.objects.get_or_create(**item)

    @staticmethod
    def add_items(items: list[dict]) -> None:
        """
        Add items to the inbox.
        """
        for item in items:
            InboxRepository.add_item(item)

    @staticmethod
    def archive_item(item_ids: list[int]) -> Inbox:
        """
        Archive an item in the inbox.
        """
        return Inbox.objects.filter(id__in=item_ids).update(
            is_archived=True, updated_at=timezone.now()
        )

    @staticmethod
    def read_item(item_id: int) -> Inbox:
        """
        Archive an item in the inbox.
        """
        return Inbox.objects.filter(id=item_id).update(
            is_read=True, updated_at=timezone.now()
        )

    @staticmethod
    def delete_items(item_ids: list[int]) -> None:
        """
        Archive an item in the inbox.
        """
        return Inbox.objects.filter(id__in=item_ids).delete()

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        """
        Get unread count of the user.
        """
        return Inbox.objects.filter(
            user_integration__user_id=user_id, is_read=False, is_archived=False
        ).count()
