from django.conf import settings
from django.db import models

from app.models import TimeStampedModel


class Integration(models.Model):
    name = models.CharField(max_length=100)
    logo = models.URLField(default=None, null=True)
    description = models.CharField(max_length=5000)
    configure_at = models.CharField(
        max_length=250, default=None, null=True, blank=False
    )

    class Meta:
        db_table = "integration"
        verbose_name = "Integration"
        verbose_name_plural = "Integrations"


class UserIntegration(TimeStampedModel):
    account_id = models.CharField(max_length=250, null=False, blank=False)
    account_display_name = models.CharField(
        max_length=250, null=False, blank=True, default=""
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False, blank=False
    )
    integration = models.ForeignKey(
        Integration,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="user_integrations",
    )
    meta_data = models.TextField(default=None, null=True, blank=False)
    configuration = models.JSONField(default=None, null=True, blank=False)
    is_revoked = models.BooleanField(default=False)

    class Meta:
        db_table = "user_integration"
        verbose_name = "User Integration"
        verbose_name_plural = "User Integration"
        unique_together = ("user", "integration", "account_id")


class IntegrationEvent(models.Model):
    """
    This model is used to keep track of unique events for an integration.
    """

    integration = models.ForeignKey(
        Integration,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="integration_events",
    )
    name = models.CharField(max_length=250, null=False, blank=False)
    description = models.TextField(default=None, null=True, blank=False)

    class Meta:
        db_table = "integration_event"
        verbose_name = "Integration Event"
        verbose_name_plural = "Integration Event"
        unique_together = ("integration", "name")


class DisabledUserIntegrationEvent(TimeStampedModel):
    """
    This model is used to keep track of disabled events for a user integration.
    """

    user_integration = models.ForeignKey(
        UserIntegration,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="disabled_user_integration_events",
    )
    integration_event = models.ForeignKey(
        IntegrationEvent,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="disabled_user_integration_events",
    )
    actions = models.JSONField(default=list, null=False, blank=False)

    class Meta:
        db_table = "disabled_user_integration_event"
        verbose_name = "Disabled User Integration Event"
        verbose_name_plural = "Disabled User Integration Event"
        unique_together = ("user_integration", "integration_event")
