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
        default=1, choices=((1, "Private"), (0, "Public"))
    )
    query_data = models.JSONField(default=dict)
    sort_order = models.FloatField(default=65535)

    def save(self, *args, **kwargs):
        if self._state.adding:
            largest_sort_order = GlobalView.objects.filter(
                workspace=self.workspace
            ).aggregate(largest=models.Max("sort_order"))["largest"]
            if largest_sort_order is not None:
                self.sort_order = largest_sort_order + 10000
        super(GlobalView, self).save(*args, **kwargs)

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
        default=0, choices=((1, "Private"), (0, "Public"))
    )
    sort_order = models.FloatField(default=65535)

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
