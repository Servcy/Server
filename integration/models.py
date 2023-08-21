from django.db import models

from app.models import TimeStampedModel
from iam.models import User


class Integration(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    logo = models.URLField(default=None, null=True)
    description = models.CharField(max_length=5000)
    meta_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "integration"
        verbose_name = "Integration"
        verbose_name_plural = "Integrations"


class UserIntegration(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    account_id = models.CharField(max_length=250, null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    integration = models.ForeignKey(
        Integration,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="user_integrations",
    )
    meta_data = models.TextField(default=None, null=True, blank=False)

    class Meta:
        db_table = "user_integration"
        verbose_name = "User Integration"
        verbose_name_plural = "User Integration"
        unique_together = ("user", "integration", "account_id")
