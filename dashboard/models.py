import uuid

from django.conf import settings
from django.db import models

from app.models import CreatorUpdaterModel, TimeStampedModel


class Dashboard(TimeStampedModel, CreatorUpdaterModel):
    name = models.CharField(max_length=255)
    description_html = models.TextField(blank=True, default="<p></p>")
    identifier = models.BigIntegerField(null=True)
    owned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dashboards",
    )
    is_default = models.BooleanField(default=False)
    type_identifier = models.CharField(
        max_length=30,
        choices=(
            ("workspace", "Workspace"),
            ("project", "Project"),
            ("home", "Home"),
            ("user", "User"),
        ),
        verbose_name="Dashboard Type",
        default="home",
    )

    class Meta:
        verbose_name = "Dashboard"
        verbose_name_plural = "Dashboards"
        db_table = "dashboard"
        ordering = ("-created_at",)


class Widget(TimeStampedModel, CreatorUpdaterModel):
    key = models.CharField(max_length=255)
    filters = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Widget"
        verbose_name_plural = "Widgets"
        db_table = "widget"
        ordering = ("-created_at",)


class DashboardWidget(TimeStampedModel, CreatorUpdaterModel):
    widget = models.ForeignKey(
        Widget,
        on_delete=models.CASCADE,
        related_name="dashboard_widgets",
    )
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name="dashboard_widgets",
    )
    is_visible = models.BooleanField(default=True)
    filters = models.JSONField(default=dict)
    properties = models.JSONField(default=dict)
    sort_order = models.FloatField(default=65535)

    class Meta:
        unique_together = ("widget", "dashboard")
        verbose_name = "Dashboard Widget"
        verbose_name_plural = "Dashboard Widgets"
        db_table = "dashboard_widget"
        ordering = ("-created_at",)


class Analytic(TimeStampedModel, CreatorUpdaterModel):
    workspace = models.ForeignKey(
        "iam.Workspace", related_name="analytics", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    query = models.JSONField()
    query_dict = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Analytic"
        verbose_name_plural = "Analytics"
        db_table = "analytic"
        ordering = ("-created_at",)
