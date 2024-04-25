from django.conf import settings
from django.db import models

from common.file_field import file_size_validator, upload_path

from .base import ProjectBaseModel


class TrackedTime(ProjectBaseModel):
    """
    TrackedTime (model): To store all the tracked time of the project
    """

    issue = models.ForeignKey(
        "project.Issue",
        on_delete=models.CASCADE,
        related_name="tracked_times",
        null=False,
    )

    description = models.TextField(
        null=True,
        default=None,
        help_text="Description of the tracked time",
    )

    is_billable = models.BooleanField(default=True)
    is_approved = models.BooleanField(
        default=False, help_text="Is time approved by an admin"
    )
    is_manually_added = models.BooleanField(
        default=False, help_text="Is time added manually by the user"
    )

    start_time = models.DateTimeField(
        auto_now_add=True,
        help_text="Start time of the tracked time",
    )
    end_time = models.DateTimeField(
        null=True,
        default=None,
        help_text="End time of the tracked time",
    )
    duration = models.DurationField(
        null=True,
        default=None,
        help_text="Duration of the tracked time, calculated from start and end time",
    )

    def save(self, *args, **kwargs):
        """
        Save the duration of the tracked time
        """
        if self.end_time:
            self.duration = self.end_time - self.start_time
        return super().save(*args, **kwargs)

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
