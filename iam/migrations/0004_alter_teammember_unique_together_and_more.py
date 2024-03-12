# Generated by Django 4.2.9 on 2024-03-12 10:37

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("iam", "0003_remove_workspacemember_company_role"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="teammember",
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name="teammember",
            name="created_by",
        ),
        migrations.RemoveField(
            model_name="teammember",
            name="member",
        ),
        migrations.RemoveField(
            model_name="teammember",
            name="team",
        ),
        migrations.RemoveField(
            model_name="teammember",
            name="updated_by",
        ),
        migrations.RemoveField(
            model_name="teammember",
            name="workspace",
        ),
        migrations.DeleteModel(
            name="Team",
        ),
        migrations.DeleteModel(
            name="TeamMember",
        ),
    ]
