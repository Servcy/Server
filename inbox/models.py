from django.db import models

from app.models import TimeStampedModel
from integration.models import UserIntegration


class InboxItem(TimeStampedModel):
    uid = models.CharField(max_length=255, unique=True, db_index=True)
    title = models.CharField(max_length=255)
    body = models.TextField(null=True, blank=False, default=None)
    is_archived = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    cause = models.CharField(max_length=255, null=True, blank=False, default=None)
    is_body_html = models.BooleanField(default=False)
    user_integration = models.ForeignKey(
        UserIntegration, on_delete=models.CASCADE, related_name="inbox_items"
    )
    category = models.CharField(max_length=255, null=True, blank=False, default=None)

    class Meta:
        db_table = "inbox_item"
        verbose_name = "Inbox Item"
        verbose_name_plural = "Inbox Items"


class GoogleMail(TimeStampedModel):
    message_id = models.CharField(max_length=255, unique=True, db_index=True)
    thread_id = models.CharField(max_length=255)
    history_id = models.CharField(max_length=255)
    snippet = models.TextField()
    size_estimate = models.IntegerField()
    payload = models.JSONField()
    label_ids = models.JSONField()
    internal_date = models.DateTimeField()
    user_integration = models.ForeignKey(
        UserIntegration, on_delete=models.CASCADE, related_name="google_mails"
    )

    class Meta:
        db_table = "google_mail"
        verbose_name = "Google Mail"
        verbose_name_plural = "Google Mails"


class OutlookMail(TimeStampedModel):
    message_id = models.CharField(max_length=255, unique=True, db_index=True)
    categories = models.JSONField()
    payload = models.JSONField()
    user_integration = models.ForeignKey(
        UserIntegration, on_delete=models.CASCADE, related_name="outlook_mails"
    )

    class Meta:
        db_table = "outlook_mail"
        verbose_name = "Outlook Mail"
        verbose_name_plural = "Outlook Mails"
