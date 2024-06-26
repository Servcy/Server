# Generated by Django 4.2.10 on 2024-04-19 06:26

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    replaces = [
        ("billing", "0001_initial"),
        ("billing", "0002_subscription_limits"),
        ("billing", "0003_subscriptionwebhookevent"),
        ("billing", "0004_subscriptionwebhookevent_event_body"),
        ("billing", "0005_remove_subscription_valid_till"),
    ]

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("iam", "0010_remove_loginotp_is_verified"),
    ]

    operations = [
        migrations.CreateModel(
            name="SubscriptionWebhookEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("event_id", models.CharField(max_length=1000, unique=True)),
                ("event_body", models.JSONField(default=dict)),
            ],
            options={
                "verbose_name": "Subscription Webhook Event",
                "verbose_name_plural": "Subscription Webhook Events",
                "db_table": "subscription_webhook_event",
            },
        ),
        migrations.CreateModel(
            name="Subscription",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("plan_details", models.JSONField(default=dict)),
                ("subscription_details", models.JSONField(default=dict)),
                (
                    "created_by",
                    models.ForeignKey(
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(app_label)s_%(class)s_created_by",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(app_label)s_%(class)s_updated_by",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subscriptions",
                        to="iam.workspace",
                    ),
                ),
                ("limits", models.JSONField(default=dict)),
            ],
            options={
                "verbose_name": "Subscription",
                "verbose_name_plural": "Subscriptions",
                "db_table": "subscription",
            },
        ),
    ]
