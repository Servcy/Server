# Generated by Django 4.2.9 on 2024-03-12 09:55

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("iam", "0002_alter_workspacemember_role_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="workspacemember",
            name="company_role",
        ),
    ]