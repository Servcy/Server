from django.db import models

from app.models import TimeStampedModel
from client.models import Client
from iam.models import User
from integration.models import UserIntegration


class Project(TimeStampedModel):
    name = models.CharField(max_length=100)
    uid = models.CharField(max_length=100, null=False, blank=False)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, null=True, blank=False, default=None
    )
    file_ids = models.JSONField(default=list)
    meta_data = models.JSONField(default=dict, null=False, blank=False)
    user_integration = models.ForeignKey(
        UserIntegration,
        on_delete=models.CASCADE,
        null=True,
        blank=False,
        default=None,
    )

    class Meta:
        db_table = "project"
        unique_together = (("user", "uid"),)
        verbose_name = "Project"
        verbose_name_plural = "Projects"
