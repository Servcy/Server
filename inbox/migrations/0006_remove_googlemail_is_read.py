# Generated by Django 4.2 on 2023-08-21 09:52

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("inbox", "0005_inboxitem_uid"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="googlemail",
            name="is_read",
        ),
    ]
