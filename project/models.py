from django.db import models

from app.models import TimeStampedModel
from iam.models import User


class Project(TimeStampedModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)

    class Meta:
        db_table = "project"
        verbose_name = "Project"
        verbose_name_plural = "Projects"


class ProjectFile(TimeStampedModel):
    file = models.FileField(upload_to="ProjectFiles", null=False, blank=False)
    name = models.CharField(max_length=100, null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)

    class Meta:
        db_table = "project_file"
        verbose_name = "Project File"
        verbose_name_plural = "Project Files"
