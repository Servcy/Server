from django.db import models

from app.models import TimeStampedModel
from iam.models import User
from inbox.models import Inbox
from integration.models import UserIntegration
from tag.models import Tag


class Document(TimeStampedModel):
    file = models.FileField(upload_to="Documents", null=True, blank=False)
    name = models.CharField(max_length=100, null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    link = models.CharField(max_length=5000, null=True, blank=False)
    user_integration = models.ForeignKey(
        UserIntegration, null=True, blank=False, on_delete=models.CASCADE
    )
    inbox_item = models.ForeignKey(
        Inbox, null=True, blank=False, on_delete=models.CASCADE
    )
    tags = models.ManyToManyField(Tag)

    class Meta:
        db_table = "document"
        verbose_name = "Document"
        verbose_name_plural = "Documents"
