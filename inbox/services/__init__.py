from inbox.models import InboxItem
from inbox.repository import InboxRepository


class InboxService:
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id

    def refresh_inbox(self) -> dict[str, list[InboxItem]]:
        """
        Collate all the services and return the results.
        """
        return self._read_inbox()

    def _read_inbox(self) -> list[InboxItem]:
        """
        Read notifications from all the services and store them in the UserInbox.
        """
        return []

    def archive_item(self, item_ids: list[int]) -> InboxItem:
        """
        Archive an item.
        """
        return InboxRepository.archive_item(item_ids=item_ids)

    def delete_item(self, item_ids: list[int]) -> InboxItem:
        """
        Delete an item.
        """
        return InboxRepository.delete_item(item_ids=item_ids)
