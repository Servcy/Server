from django.conf import settings
from django.db import models

from common.file_field import file_size_validator, upload_path

from .base import ProjectBaseModel


class TrackedTime(ProjectBaseModel):
    """
    TrackedTime (model): To store all the tracked time of the project
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tracked_times",
    )
    issue = models.ForeignKey(
        "project.Issue",
        on_delete=models.CASCADE,
        related_name="tracked_times",
        null=False,
    )
    cycle = models.ForeignKey(
        "project.Cycle",
        on_delete=models.CASCADE,
        related_name="tracked_times",
        null=True,
        default=None,
    )
    module = models.ForeignKey(
        "project.Module",
        on_delete=models.CASCADE,
        related_name="tracked_times",
        null=True,
        default=None,
    )
    is_billable = models.BooleanField(default=True)
    start_time = models.DateTimeField(
        auto_now_add=True,
        help_text="Start time of the tracked time",
    )
    end_time = models.DateTimeField(
        null=True,
        default=None,
        help_text="End time of the tracked time",
    )
    is_approved = models.BooleanField(
        default=False, help_text="Is time approved by an admin"
    )
    description = models.TextField(
        null=True,
        default=None,
        help_text="Description of the tracked time",
    )

    class Meta:
        verbose_name = "Tracked Time"
        verbose_name_plural = "Tracked Times"
        db_table = "tracked_time"
        ordering = ("-created_at",)


class TrackedTimeAttachment(ProjectBaseModel):
    meta_data = models.JSONField(default=dict)
    file = models.FileField(
        upload_to=upload_path,
        validators=[
            file_size_validator,
        ],
    )
    tracked_time = models.ForeignKey(
        TrackedTime,
        on_delete=models.CASCADE,
        related_name="attachments",
        null=False,
    )

    class Meta:
        verbose_name = "Tracked Time Attachment"
        verbose_name_plural = "Tracked Time Attachments"
        db_table = "tracked_time_attachment"
        ordering = ("-created_at",)
