from django.db import models


class Integration(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    logo = models.URLField(default=None, null=True)
    description = models.CharField(max_length=5000)
    meta_data = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "integration"
        verbose_name = "Integration"
        verbose_name_plural = "Integrations"
        ordering = ["id"]
