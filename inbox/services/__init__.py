from inbox.services.google import GoogleMailService


class InboxService:
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id

    def sync_inbox(self) -> None:
        fetch_new_unread_mails = GoogleMailService.fetch_new_unread_mails(
            user_id=self.user_id
        )
