from django.db import models
from django.utils.translation import gettext_lazy as _

from app.models import TimeStampedModel
from iam.models import User


class Client(TimeStampedModel):
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, null=True)
    phone = models.CharField(max_length=255, null=True)
    address = models.CharField(max_length=255, null=True)
    notes = models.TextField(null=True)
    website = models.CharField(max_length=255, null=True)
    file_ids = models.JSONField(default=list)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    avatar = models.ForeignKey(
        "Avatar",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="client_avatar",
    )

    def __str__(self):
        return self.name

    class Meta:
        unique_together = (("user", "name"),)
        db_table = "client"
        verbose_name = "Client"
        verbose_name_plural = "Clients"


class Avatar(TimeStampedModel):
    file = models.FileField(upload_to="Avatars", null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)

    class Meta:
        db_table = "avatar"
        verbose_name = "Avatar"
        verbose_name_plural = "Avatars"
