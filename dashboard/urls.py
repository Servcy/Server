from django.urls import path

from dashboard.views import (
    AnalyticsEndpoint,
    AnalyticViewViewset,
    DashboardEndpoint,
    DefaultAnalyticsEndpoint,
    ExportAnalyticsEndpoint,
    WidgetsEndpoint,
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
        AnalyticsEndpoint.as_view(),
        name="servcy-analytics",
    ),
    path(
        "<str:workspace_slug>/analytics/export",
        ExportAnalyticsEndpoint.as_view(),
        name="export-analytics",
    ),
    path(
        "<str:workspace_slug>/analytics/view",
        AnalyticViewViewset.as_view({"get": "list", "post": "create"}),
        name="analytic-view",
    ),
    path(
        "<str:workspace_slug>/analytics/default",
        DefaultAnalyticsEndpoint.as_view(),
        name="default-analytics",
    ),
]
