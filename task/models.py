from django.db import models

from app.models import TimeStampedModel
from iam.models import User


class Task(TimeStampedModel):
    uid = models.CharField(
        max_length=100, null=False, blank=False, unique=True, db_index=True
    )
    name = models.CharField(max_length=100)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    file_ids = models.JSONField(default=list)
    meta_data = models.JSONField(default=dict, null=True, blank=True)
    project_uid = models.CharField(max_length=100, null=False, blank=False)

    class Meta:
        db_table = "task"
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
