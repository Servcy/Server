# Generated by Django 4.2.10 on 2024-04-20 07:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("project", "0021_projectmember_rate"),
    ]

    operations = [
        migrations.AlterField(
            model_name="projectmemberrate",
            name="per_hour_or_per_project",
            field=models.BooleanField(
                default=True,
                help_text="Is rate per hour or per project, default is per hour",
            ),
        ),
    ]