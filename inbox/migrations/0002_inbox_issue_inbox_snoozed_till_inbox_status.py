# Generated by Django 4.2.9 on 2024-03-03 07:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("project", "0001_initial"),
        ("inbox", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="inbox",
            name="issue",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="issue_inbox",
                to="project.issue",
            ),
        ),
        migrations.AddField(
            model_name="inbox",
            name="snoozed_till",
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name="inbox",
            name="status",
            field=models.IntegerField(
                choices=[
                    (-2, "Pending"),
                    (-1, "Rejected"),
                    (0, "Snoozed"),
                    (1, "Accepted"),
                    (2, "Duplicate"),
                ],
                default=-2,
            ),
        ),
    ]