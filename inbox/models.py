from django.db import models

from app.models import TimeStampedModel
from integration.models import UserIntegration


class InboxItem(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    body = models.TextField(null=True, blank=False, default=None)
    is_archived = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    user_integration = models.ForeignKey(
        UserIntegration, on_delete=models.CASCADE, related_name="inbox_items"
    )

    class Meta:
        db_table = "inbox_item"
        verbose_name = "Inbox Item"
        verbose_name_plural = "Inbox Items"


class GoogleMail(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    message_id = models.CharField(max_length=255, unique=True, db_index=True)
    thread_id = models.CharField(max_length=255)
    history_id = models.CharField(max_length=255)
    snippet = models.TextField()
    size_estimate = models.IntegerField()
    payload = models.JSONField()
    label_ids = models.JSONField()
    internal_date = models.DateTimeField()
    is_read = models.BooleanField(default=False)
    user_integration = models.ForeignKey(
        UserIntegration, on_delete=models.CASCADE, related_name="google_mails"
    )

    class Meta:
        db_table = "google_mail"
        verbose_name = "Google Mail"
        verbose_name_plural = "Google Mails"
