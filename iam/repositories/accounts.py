from django.conf import settings

from iam.models import User


class AccountsRepository:
    def __init__(self, input: str, input_type: str):
        self.input = input
        self.input_type = input_type

    def create(self, input: str = None, input_type: str = None):
        input = input or self.input
        input_type = input_type or self.input_type
        user = User.objects.create_user(
            email=input if input_type == "email" else None,
            phone_number=f"+{input}" if input_type == "phone_number" else None,
            username=input if input_type == "email" else f"+{input}",
            password=None,
        )
        return user

    def get(self, input: str = None, input_type: str = None):
        try:
            input = input or self.input
            input_type = input_type or self.input_type
            user = User.objects.get(
                username=input if input_type == "email" else f"+{input}"
            )
        except User.DoesNotExist:
            user = None
        return user
