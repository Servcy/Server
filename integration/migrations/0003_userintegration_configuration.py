# Generated by Django 4.2 on 2023-08-29 07:01

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("integration", "0002_userintegration_account_display_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="userintegration",
            name="configuration",
            field=models.JSONField(default=None, null=True),
        ),
    ]