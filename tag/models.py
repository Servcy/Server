from django.conf import settings
from django.db import models

from app.models import TimeStampedModel


class Tag(TimeStampedModel):
    name = models.CharField(max_length=100, null=False, blank=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False, blank=False
    )

    class Meta:
        db_table = "tag"
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        unique_together = ("name", "user")
