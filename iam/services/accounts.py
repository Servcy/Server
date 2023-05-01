from iam.repositories.accounts import AccountsRepository


class AccountsService:
    def __init__(self, email, phone_number):
        self.email = email
        self.phone_number = phone_number
        self.account_repository = AccountsRepository(email, phone_number)

    def create_user_account(self):
        user = self.account_repository.get(self.email, self.phone_number)
        if not user:
            user = self.account_repository.create(self.email, self.phone_number)
        return user
