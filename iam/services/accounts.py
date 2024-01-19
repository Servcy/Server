from iam.repositories.accounts import AccountsRepository
from mails import SendGridEmail


class AccountsService:
    def __init__(self, input: str, input_type: str):
        self.input = input
        self.input_type = input_type
        self.account_repository = AccountsRepository(input, input_type)

    def create_user_account(self):
        user = self.account_repository.get()
        if not user:
            user = self.account_repository.create()
            sendgrid_email = SendGridEmail("megham@servcy.com")
            sendgrid_email.send_new_signup_notification(
                {
                    "user_email": user.email,
                    "user_phone_number": user.phone_number,
                }
            )
        return user
