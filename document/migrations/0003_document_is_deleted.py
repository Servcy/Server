# Generated by Django 4.2.9 on 2024-03-13 08:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("document", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="is_deleted",
            field=models.BooleanField(default=False),
        ),
    ]
