from django.conf import settings
from django.db import models

from app.models import CreatorUpdaterModel, TimeStampedModel

from .base import ProjectBaseModel


class GlobalView(TimeStampedModel, CreatorUpdaterModel):
    workspace = models.ForeignKey(
        "iam.Workspace", on_delete=models.CASCADE, related_name="global_views"
    )
    name = models.CharField(max_length=255, verbose_name="View Name")
    description = models.TextField(verbose_name="View Description", blank=True)
    query = models.JSONField(verbose_name="View Query")
    access = models.PositiveSmallIntegerField(
        default=1, choices=((0, "Private"), (1, "Public"))
    )
    query_data = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Global View"
        verbose_name_plural = "Global Views"
        db_table = "global_view"
        ordering = ("-created_at",)


class IssueView(ProjectBaseModel):
    name = models.CharField(max_length=255, verbose_name="View Name")
    description = models.TextField(verbose_name="View Description", blank=True)
    query = models.JSONField(verbose_name="View Query")
    filters = models.JSONField(default=dict)
    display_filters = models.JSONField(default=dict)
    display_properties = models.JSONField(default=dict)
    access = models.PositiveSmallIntegerField(
        default=1, choices=((0, "Private"), (1, "Public"))
    )

    class Meta:
        verbose_name = "Issue View"
        verbose_name_plural = "Issue Views"
        db_table = "issue_view"
        ordering = ("-created_at",)


class IssueViewFavorite(ProjectBaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_view_favorites",
    )
    view = models.ForeignKey(
        IssueView, on_delete=models.CASCADE, related_name="view_favorites"
    )

    class Meta:
        unique_together = ["view", "user"]
        verbose_name = "View Favorite"
        verbose_name_plural = "View Favorites"
        db_table = "view_favorite"
        ordering = ("-created_at",)
