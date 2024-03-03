# Generated by Django 4.2.9 on 2024-03-03 07:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("integration", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Inbox",
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
                ("uid", models.CharField(max_length=255)),
                ("title", models.CharField(max_length=255)),
                ("body", models.TextField(default=None, null=True)),
                ("is_archived", models.BooleanField(default=False)),
                ("is_read", models.BooleanField(default=False)),
                ("cause", models.CharField(default=None, max_length=10000, null=True)),
                ("is_body_html", models.BooleanField(default=False)),
                ("category", models.CharField(default=None, max_length=255, null=True)),
                ("i_am_mentioned", models.BooleanField(default=False)),
                ("attachments", models.JSONField(default=None, null=True)),
                (
                    "user_integration",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="inbox_items",
                        to="integration.userintegration",
                    ),
                ),
            ],
            options={
                "verbose_name": "Inbox",
                "db_table": "inbox",
                "unique_together": {("uid", "user_integration")},
            },
        ),
    ]
