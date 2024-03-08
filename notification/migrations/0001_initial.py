# Generated by Django 4.2.9 on 2024-03-08 23:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("project", "0001_initial"),
        ("iam", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserNotificationPreference",
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
                ("property_change", models.BooleanField(default=True)),
                ("state_change", models.BooleanField(default=True)),
                ("comment", models.BooleanField(default=True)),
                ("mention", models.BooleanField(default=True)),
                ("issue_completed", models.BooleanField(default=True)),
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
                    "project",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="project_notification_preferences",
                        to="project.project",
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
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notification_preferences",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "workspace",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="workspace_notification_preferences",
                        to="iam.workspace",
                    ),
                ),
            ],
            options={
                "verbose_name": "UserNotificationPreference",
                "verbose_name_plural": "UserNotificationPreferences",
                "db_table": "user_notification_preference",
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="Notification",
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
                ("data", models.JSONField(null=True)),
                ("entity_identifier", models.BigIntegerField(null=True)),
                ("entity_name", models.CharField(max_length=255)),
                ("title", models.TextField()),
                ("message", models.JSONField(null=True)),
                ("message_html", models.TextField(blank=True, default="<p></p>")),
                ("message_stripped", models.TextField(blank=True, null=True)),
                ("sender", models.CharField(max_length=255)),
                ("read_at", models.DateTimeField(null=True)),
                ("snoozed_till", models.DateTimeField(null=True)),
                ("archived_at", models.DateTimeField(null=True)),
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
                    "project",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to="project.project",
                    ),
                ),
                (
                    "receiver",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="received_notifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "triggered_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="triggered_notifications",
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
                        related_name="notifications",
                        to="iam.workspace",
                    ),
                ),
            ],
            options={
                "verbose_name": "Notification",
                "verbose_name_plural": "Notifications",
                "db_table": "notification",
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="EmailNotificationLog",
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
                ("entity_identifier", models.BigIntegerField(null=True)),
                ("entity_name", models.CharField(max_length=255)),
                ("data", models.JSONField(null=True)),
                ("processed_at", models.DateTimeField(null=True)),
                ("sent_at", models.DateTimeField(null=True)),
                ("entity", models.CharField(max_length=200)),
                ("old_value", models.CharField(blank=True, max_length=300, null=True)),
                ("new_value", models.CharField(blank=True, max_length=300, null=True)),
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
                    "receiver",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="email_notifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "triggered_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="triggered_emails",
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
            ],
            options={
                "verbose_name": "Email Notification Log",
                "verbose_name_plural": "Email Notification Logs",
                "db_table": "email_notification_log",
                "ordering": ("-created_at",),
            },
        ),
    ]
