from django.conf import settings
from django.db import models

from .base import ProjectBaseModel


class Module(ProjectBaseModel):
    name = models.CharField(max_length=255, verbose_name="Module Name")
    description = models.TextField(verbose_name="Module Description", blank=True)
    description_text = models.JSONField(
        verbose_name="Module Description Rich Text", blank=True, null=True
    )
    description_html = models.JSONField(
        verbose_name="Module Description HTML", blank=True, null=True
    )
    start_date = models.DateField(null=True)
    archived_at = models.DateTimeField(null=True)
    sort_order = models.FloatField(default=65535)
    target_date = models.DateField(null=True)
    status = models.CharField(
        choices=(
            ("backlog", "Backlog"),
            ("planned", "Planned"),
            ("in-progress", "In Progress"),
            ("paused", "Paused"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ),
        default="planned",
        max_length=20,
    )
    lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="module_leads",
        null=True,
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="module_members",
        through="ModuleMember",
        through_fields=("module", "member"),
    )
    view_props = models.JSONField(default=dict)

    def save(self, *args, **kwargs):
        if self._state.adding:
            smallest_sort_order = Module.objects.filter(project=self.project).aggregate(
                smallest=models.Min("sort_order")
            )["smallest"]
            if smallest_sort_order is not None:
                self.sort_order = smallest_sort_order - 10000
        super(Module, self).save(*args, **kwargs)

    class Meta:
        unique_together = ["name", "project"]
        verbose_name = "Module"
        verbose_name_plural = "Modules"
        db_table = "module"
        ordering = ("-created_at",)


class ModuleMember(ProjectBaseModel):
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ["module", "member"]
        verbose_name = "Module Member"
        verbose_name_plural = "Module Members"
        db_table = "module_member"
        ordering = ("-created_at",)


class ModuleIssue(ProjectBaseModel):
    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="issue_module"
    )
    issue = models.ForeignKey(
        "project.Issue", on_delete=models.CASCADE, related_name="issue_module"
    )

    class Meta:
        unique_together = ["issue", "module"]
        verbose_name = "Module Issue"
        verbose_name_plural = "Module Issues"
        db_table = "module_issue"
        ordering = ("-created_at",)


class ModuleLink(ProjectBaseModel):
    title = models.CharField(max_length=255, blank=True, null=True)
    url = models.URLField()
    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="link_module"
    )
    metadata = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Module Link"
        verbose_name_plural = "Module Links"
        db_table = "module_link"
        ordering = ("-created_at",)


class ModuleFavorite(ProjectBaseModel):
    """_summary_
    ModuleFavorite (model): To store all the module favorite of the user
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="module_favorites",
    )
    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="module_favorites"
    )

    class Meta:
        unique_together = ["module", "user"]
        verbose_name = "Module Favorite"
        verbose_name_plural = "Module Favorites"
        db_table = "module_favorite"
        ordering = ("-created_at",)


class ModuleUserProperties(ProjectBaseModel):
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="module_user_properties",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="module_user_properties",
    )
    filters = models.JSONField(default=dict)
    display_filters = models.JSONField(default=dict)
    display_properties = models.JSONField(default=dict)

    class Meta:
        unique_together = ["module", "user"]
        verbose_name = "Module User Property"
        verbose_name_plural = "Module User Property"
        db_table = "module_user_property"
        ordering = ("-created_at",)
