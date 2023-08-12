from django.db import models

from app.models import TimeStampedModel


class Integration(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    logo = models.URLField(default=None, null=True)
    description = models.CharField(max_length=5000)
    meta_data = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "integration"
        verbose_name = "Integration"
        verbose_name_plural = "Integrations"
        ordering = ["id"]


class IntegrationUser(TimeStampedModel):
    id = models.AutoField(primary_key=True)

    account_id = models.CharField(max_length=250, null=False, blank=False)
    user_id = models.IntegerField(null=False, blank=False)
    integration_id = models.IntegerField(null=False, blank=False)

    meta_data = models.TextField(default=None, null=True, blank=False)

    class Meta:
        db_table = "integration_user"
        verbose_name = "Integration User"
        verbose_name_plural = "Integration Users"
        ordering = ["id"]
        unique_together = ("user_id", "integration_id", "account_id")
