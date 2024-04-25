from django.urls import path

from dashboard.views import (
    DashboardEndpoint,
    DefaultWorkspaceStatsEndpoint,
    ExportAnalyticsEndpoint,
    TimesheetStatsEndpoint,
    WidgetsEndpoint,
    WorkspaceStatsEndpoint,
)

urlpatterns = [
    # Dashboard
    path(
        "<str:workspace_slug>",
        DashboardEndpoint.as_view(),
        name="dashboard",
    ),
    path(
        "<str:workspace_slug>/<int:dashboard_id>",
        DashboardEndpoint.as_view(),
        name="dashboard",
    ),
    # Widgets
    path(
        "<int:dashboard_id>/widgets/<int:widget_id>/",
        WidgetsEndpoint.as_view(),
        name="widgets",
    ),
    # Analytics
    path(
        "<str:workspace_slug>/analytics",
        WorkspaceStatsEndpoint.as_view(),
        name="servcy-analytics",
    ),
    path(
        "<str:workspace_slug>/export-analytics",
        ExportAnalyticsEndpoint.as_view(),
        name="export-analytics",
    ),
    path(
        "<str:workspace_slug>/default-analytics",
        DefaultWorkspaceStatsEndpoint.as_view(),
        name="default-analytics",
    ),
    path(
        "<str:workspace_slug>/timesheet-analytics/<str:view_key>",
        TimesheetStatsEndpoint.as_view(),
        name="timesheet-analytics",
    ),
]
