import logging
import traceback

from iam.repositories.accounts import AccountsRepository
from mails import SendGridEmail

logger = logging.getLogger(__name__)


class AccountsService:
    def __init__(self, input: str, input_type: str):
        self.input = input
        self.input_type = input_type
        self.account_repository = AccountsRepository(input, input_type)

    def create_user_account(self):
        user = self.account_repository.get()
        if not user:
            user = self.account_repository.create()
            try:
                sendgrid_email = SendGridEmail("megham@servcy.com")
                sendgrid_email.send_new_signup_notification(
                    {
                        "user_email": user.email,
                        "user_phone_number": user.phone_number,
                    }
                )
            except Exception:
                logger.exception(
                    "An error occurred while sending new signup notification.",
                    extra={
                        "traceback": traceback.format_exc(),
                    },
                )
        return user
