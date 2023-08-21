from inbox.models import InboxItem
from inbox.repository import GoogleMailRepository, InboxRepository


class InboxService:
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id

    def sync_inbox(self) -> dict[str, list[InboxItem]]:
        """
        Collate all the services and return the results.
        """
        mails = self._read_mails()
        notifications = self._read_notifications()
        messages = self._read_messages()
        comments = self._read_comments()
        return {
            "mails": mails,
            "notifications": notifications,
            "messages": messages,
            "comments": comments,
        }

    def _read_mails(self) -> list[InboxItem]:
        """
        Read mails from all the services and store them in the UserInbox.
        """
        google_mails = GoogleMailRepository.read_mails(
            filters={
                "user_integration__user_id": self.user_id,
                "is_read": False,
            },
            values=["id", "payload", "created_at", "user_integration__account_id"],
        )
        inbox_items = InboxRepository.add_items(
            items=[
                {
                    "title": mail["payload"]["headers"][0]["value"],
                    "body": mail["payload"]["body"]["data"],
                    "user_integration_id": mail["user_integration__account_id"],
                    "created_at": mail["created_at"],
                }
                for mail in google_mails
            ],
        )
        return inbox_items

    def _read_notifications(self) -> list[InboxItem]:
        """
        Read notifications from all the services and store them in the UserInbox.
        """
        return []

    def _read_messages(self) -> list[InboxItem]:
        """
        Read messages from all the services and store them in the UserInbox.
        """
        return []

    def _read_comments(self) -> list[InboxItem]:
        """
        Read comments from all the services and store them in the UserInbox.
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
