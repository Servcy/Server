# Generated by Django 4.2.9 on 2024-02-13 12:28

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("integration", "0014_alter_disableduserintegrationevent_actions"),
        ("inbox", "0009_inbox_attachments"),
    ]

    operations = [
        migrations.AlterField(
            model_name="inbox",
            name="uid",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name="inbox",
            unique_together={("uid", "user_integration")},
        ),
    ]