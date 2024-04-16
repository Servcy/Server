from django.db import models

from app.models import CreatorUpdaterModel, TimeStampedModel


class Subscription(TimeStampedModel, CreatorUpdaterModel):
    workspace = models.ForeignKey(
        "iam.Workspace",
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    is_active = models.BooleanField(default=True)
    plan_details = models.JSONField(default=dict)
    subscription_details = models.JSONField(default=dict)
    valid_till = models.DateTimeField(null=True, default=None)
    limits = models.JSONField(default=dict)

    class Meta:
        db_table = "subscription"
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
