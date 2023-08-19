from django.db import models

from app.models import TimeStampedModel
from integration.models import IntegrationUser


class GoogleMail(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)

    message_id = models.CharField(max_length=255)
    thread_id = models.CharField(max_length=255)
    history_id = models.CharField(max_length=255)
    data = models.JSONField()
    integration_user = models.ForeignKey(
        IntegrationUser, on_delete=models.CASCADE, related_name="google_mails"
    )

    class Meta:
        db_table = "google_mail"
        verbose_name = "Google Mail"
        verbose_name_plural = "Google Mails"
