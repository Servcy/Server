from django.utils import timezone

from iam.models import User
from notification.models import UserNotificationPreference


class AccountsRepository:
    def __init__(self, input: str, input_type: str, display_name: str = ""):
        self.input = input
        self.input_type = input_type
        self.display_name = display_name

    def create(self):
        user = User.objects.create_user(
            email=self.input if self.input_type == "email" else None,
            phone_number=(
                f"+{self.input}" if self.input_type == "phone_number" else None
            ),
            username=self.input if self.input_type == "email" else f"+{self.input}",
            display_name=self.display_name,
            password=None,
        )
        UserNotificationPreference.objects.create(
            user=user,
            property_change=False,
            state_change=False,
            comment=False,
            mention=False,
            issue_completed=False,
        )
        return user

    def get(self):
        try:
            user = User.objects.get(
                username=self.input if self.input_type == "email" else f"+{input}"
            )
        except User.DoesNotExist:
            user = None
        return user

    def update_last_login(self, user):
        user.last_login = timezone.now()
        user.save()
        return user
