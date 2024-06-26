from django.db import models

from app.models import CreatorUpdaterModel, TimeStampedModel


class Subscription(TimeStampedModel, CreatorUpdaterModel):
    workspace = models.ForeignKey(
        "iam.Workspace",
        on_delete=models.CASCADE,
        related_name="subscriptions",
        default=None,
        null=True,
    )
    is_active = models.BooleanField(default=True)
    plan_details = models.JSONField(default=dict)
    customer_details = models.JSONField(default=dict)
    subscription_id = models.CharField(max_length=1000, unique=True)
    limits = models.JSONField(default=dict)

    class Meta:
        db_table = "subscription"
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"


class SubscriptionWebhookEvent(models.Model):
    event_id = models.CharField(max_length=1000, unique=True)

    class Meta:
        db_table = "subscription_webhook_event"
        verbose_name = "Subscription Webhook Event"
        verbose_name_plural = "Subscription Webhook Events"
