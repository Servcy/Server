from django.conf import settings
from django.db import models

from .base import ProjectBaseModel


class Cycle(ProjectBaseModel):
    name = models.CharField(max_length=255, verbose_name="Cycle Name")
    description = models.TextField(verbose_name="Cycle Description", blank=True)
    start_date = models.DateField(verbose_name="Start Date", blank=True, null=True)
    end_date = models.DateField(verbose_name="End Date", blank=True, null=True)
    sort_order = models.FloatField(default=65535)
    owned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_by_cycle",
    )
    view_props = models.JSONField(default=dict)
    progress_snapshot = models.JSONField(default=dict)

    def save(self, *args, **kwargs):
        if self._state.adding:
            smallest_sort_order = Cycle.objects.filter(project=self.project).aggregate(
                smallest=models.Min("sort_order")
            )["smallest"]
            if smallest_sort_order is not None:
                self.sort_order = smallest_sort_order - 10000
        super(Cycle, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Cycle"
        verbose_name_plural = "Cycles"
        db_table = "cycle"
        ordering = ("-created_at",)


class CycleIssue(ProjectBaseModel):
    """
    Cycle Issues
    """

    issue = models.OneToOneField(
        "project.Issue", on_delete=models.CASCADE, related_name="issue_cycle"
    )
    cycle = models.ForeignKey(
        Cycle, on_delete=models.CASCADE, related_name="issue_cycle"
    )

    class Meta:
        verbose_name = "Cycle Issue"
        verbose_name_plural = "Cycle Issues"
        db_table = "cycle_issue"
        ordering = ("-created_at",)


class CycleFavorite(ProjectBaseModel):
    """
    CycleFavorite (model): To store all the cycle favorite of the user
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cycle_favorites",
    )
    cycle = models.ForeignKey(
        Cycle, on_delete=models.CASCADE, related_name="cycle_favorites"
    )

    class Meta:
        unique_together = ["cycle", "user"]
        verbose_name = "Cycle Favorite"
        verbose_name_plural = "Cycle Favorites"
        db_table = "cycle_favorite"
        ordering = ("-created_at",)


class CycleUserProperties(ProjectBaseModel):
    cycle = models.ForeignKey(
        Cycle,
        on_delete=models.CASCADE,
        related_name="cycle_user_properties",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cycle_user_properties",
    )
    filters = models.JSONField(default=dict)
    display_filters = models.JSONField(default=dict)
    display_properties = models.JSONField(default=dict)

    class Meta:
        unique_together = ["cycle", "user"]
        verbose_name = "Cycle User Property"
        verbose_name_plural = "Cycle User Properties"
        db_table = "cycle_user_property"
        ordering = ("-created_at",)
