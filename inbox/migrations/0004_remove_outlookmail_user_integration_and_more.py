# Generated by Django 4.2.4 on 2023-09-13 11:44

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("inbox", "0003_alter_inboxitem_cause"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="outlookmail",
            name="user_integration",
        ),
        migrations.DeleteModel(
            name="GoogleMail",
        ),
        migrations.DeleteModel(
            name="OutlookMail",
        ),
    ]
