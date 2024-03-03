from django.conf import settings
from django.db import models

from app.models import TimeStampedModel
from common.file_field import file_size_validator, upload_path


class Document(TimeStampedModel):
    name = models.CharField(max_length=100)
    file = models.FileField(
        upload_to=upload_path,
        validators=[file_size_validator],
        null=True,
        default=None,
    )
    link = models.URLField(max_length=200, null=True, default=None)
    meta_data = models.JSONField(default=dict)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    workspace = models.ForeignKey(
        "iam.Workspace",
        on_delete=models.CASCADE,
        null=True,
        related_name="assets",
        default=None,
    )

    class Meta:
        db_table = "document"
        verbose_name = "Document"
        verbose_name_plural = "Documents"
