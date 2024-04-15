# Generated by Django 4.2.10 on 2024-04-10 15:48

from django.db import migrations, models

import project.models.project


class Migration(migrations.Migration):
    dependencies = [
        ("project", "0010_remove_projecttemplate_states_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="projecttemplate",
            name="estimates",
            field=models.JSONField(
                default=project.models.project.get_default_estimates
            ),
        ),
        migrations.AlterField(
            model_name="projecttemplate",
            name="labels",
            field=models.JSONField(default=project.models.project.get_default_labels),
        ),
    ]