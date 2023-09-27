from django.db import models

from app.models import TimeStampedModel
from iam.models import User


class Project(TimeStampedModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    file_ids = models.JSONField(default=list)

    class Meta:
        db_table = "project"
        verbose_name = "Project"
        verbose_name_plural = "Projects"
