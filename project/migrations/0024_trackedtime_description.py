# Generated by Django 4.2.10 on 2024-04-22 04:10

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("project", "0023_alter_projectmemberrate_unique_together_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="trackedtime",
            name="description",
            field=models.TextField(
                default=None, help_text="Description of the tracked time", null=True
            ),
        ),
    ]
