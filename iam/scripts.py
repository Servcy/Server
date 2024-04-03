from datetime import timedelta

from django.utils import timezone

from iam.models import LoginOTP


def remove_stale_otps():
    LoginOTP.objects.filter(
        created_at__lt=timezone.now() - timedelta(minutes=5)
    ).delete()
