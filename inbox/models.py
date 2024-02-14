from django.db import models

from app.models import TimeStampedModel
from integration.models import UserIntegration
from iam.models import User


class Inbox(TimeStampedModel):
    uid = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    body = models.TextField(null=True, blank=False, default=None)
    is_archived = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    cause = models.CharField(max_length=10000, null=True, blank=False, default=None)
    is_body_html = models.BooleanField(default=False)
    user_integration = models.ForeignKey(
        UserIntegration, on_delete=models.CASCADE, related_name="inbox_items"
    )
    category = models.CharField(max_length=255, null=True, blank=False, default=None)
    i_am_mentioned = models.BooleanField(default=False)
    attachments = models.JSONField(null=True, blank=False, default=None)

    class Meta:
        db_table = "inbox"
        verbose_name = "Inbox"
        unique_together = ("uid", "user_integration")


class BlockedEmail(TimeStampedModel):
    email = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = "blocked_email"
        verbose_name = "Blocked Email"
        unique_together = ("email", "user")
