from inbox.repository import GoogleMailRepository


class InboxService:
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id

    def sync_inbox(self) -> None:
        """
        Collate all the services and return the results.
        results can be of type:
            - mails (google/yahoo/outlook)
            - messages
            - notifications
        """
        google_mails = GoogleMailRepository.read_google_mails(
            filters={
                "user_integration__user_id": self.user_id,
                "is_read": False,
            },
            values=["id", "payload", "created_at", "user_integration__account_id"],
        )
        return list(google_mails)
