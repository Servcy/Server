from iam.models import User


class AccountsRepository:
    def __init__(self, email, phone_number):
        self.email = email
        self.phone_number = phone_number

    def create(self, email: str, phone_number: str) -> User:
        user = User.objects.create_user(
            email=email,
            phone_number=phone_number,
            username=email,
            password=None,
        )
        return user

    def get(self, email: str, phone_number: str) -> User:
        try:
            user = User.objects.get(email=email, phone_number=phone_number)
        except User.DoesNotExist:
            user = None
        return user
