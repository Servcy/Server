# Generated by Django 4.2 on 2023-08-12 07:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("integration", "0001_initial_squashed_0002_integration_logo"),
    ]

    operations = [
        migrations.CreateModel(
            name="IntegrationUser",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("user_id", models.IntegerField()),
                ("integration_id", models.IntegerField()),
                ("meta_data", models.TextField(default=None, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Integration User",
                "verbose_name_plural": "Integration Users",
                "db_table": "integration_user",
                "ordering": ["id"],
            },
        ),
    ]