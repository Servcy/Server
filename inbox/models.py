from django.db import models

from app.models import TimeStampedModel


class Inbox(TimeStampedModel):
    uid = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    body = models.TextField(null=True, blank=False, default=None)
    is_archived = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    cause = models.CharField(max_length=10000, null=True, blank=False, default=None)
    is_body_html = models.BooleanField(default=False)
    user_integration = models.ForeignKey(
        "integration.UserIntegration",
        on_delete=models.CASCADE,
        related_name="inbox_items",
    )
    category = models.CharField(max_length=255, null=True, blank=False, default=None)
    i_am_mentioned = models.BooleanField(default=False)
    attachments = models.JSONField(null=True, blank=False, default=None)
    # issue = models.ForeignKey(
    #     "project.Issue", related_name="issue_inbox", on_delete=models.CASCADE
    # )
    status = models.IntegerField(
        choices=(
            (-2, "Pending"),
            (-1, "Rejected"),
            (0, "Snoozed"),
            (1, "Accepted"),
            (2, "Duplicate"),
        ),
        default=-2,
    )
    snoozed_till = models.DateTimeField(null=True)

    class Meta:
        db_table = "inbox"
        verbose_name = "Inbox"
        unique_together = ("uid", "user_integration")
