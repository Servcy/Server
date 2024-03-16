# Generated by Django 4.2.9 on 2024-03-16 10:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("project", "0004_state_default"),
    ]

    operations = [
        migrations.AlterField(
            model_name="issueview",
            name="project",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="project_%(class)s",
                to="project.project",
            ),
        ),
    ]
