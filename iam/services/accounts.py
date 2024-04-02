import logging
import traceback
from random import randint

from django.conf import settings

from iam.repositories.accounts import AccountsRepository
from mails import SendGridEmail

logger = logging.getLogger(__name__)


class AccountsService:
    def __init__(self, input: str, input_type: str):
        self.input = input
        self.input_type = input_type
        self.account_repository = AccountsRepository(input, input_type)

    @staticmethod
    def verify_login_otp(email: str, otp: int) -> bool:
        return AccountsRepository.verify_login_otp(email, otp)

    def create_login_otp(self) -> int:
        otp = randint(100000, 999999)
        self.account_repository.create_login_otp(otp)
        return otp

    def create_user_account(self):
        user = self.account_repository.get()
        if not user:
            user = self.account_repository.create()
            if settings.DEBUG:
                return user
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
        self.account_repository.update_last_login(user)
        return user
