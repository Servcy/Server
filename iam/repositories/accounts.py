from django.utils import timezone

from iam.models import LoginOTP, User
from notification.models import UserNotificationPreference


class AccountsRepository:
    def __init__(self, input: str, input_type: str):
        self.input = input
        self.input_type = input_type

    def create(self, utm_source, utm_medium, utm_campaign):
        user = User.objects.create_user(
            email=self.input if self.input_type == "email" else None,
            phone_number=(
                f"+{self.input}" if self.input_type == "phone_number" else None
            ),
            username=self.input if self.input_type == "email" else f"+{self.input}",
            password=None,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
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
        user.is_active = True
        user.save()
        return user

    def create_login_otp(self, otp: int):
        LoginOTP.objects.create(input=self.input, otp=otp)

    @staticmethod
    def verify_login_otp(email, otp):
        try:
            login_otp = LoginOTP.objects.get(input=email, otp=otp)
        except LoginOTP.DoesNotExist:
            return False
        login_otp.delete()
        return True
