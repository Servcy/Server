# Generated by Django 4.2.9 on 2024-03-20 06:21

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("iam", "0007_alter_workspace_logo"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="workspacemember",
            unique_together={("member", "workspace")},
        ),
    ]
