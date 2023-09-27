from django.db import models

from app.models import TimeStampedModel
from iam.models import User


class Document(TimeStampedModel):
    file = models.FileField(upload_to="Documents", null=False, blank=False)
    name = models.CharField(max_length=100, null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)

    class Meta:
        db_table = "document"
        verbose_name = "Document"
        verbose_name_plural = "Documents"
