from django.urls import include, path
from rest_framework import routers

from dashboard.views import (
    AnalyticsEndpoint,
    AnalyticViewViewset,
    DashboardEndpoint,
    DefaultAnalyticsEndpoint,
    ExportAnalyticsEndpoint,
    WidgetsEndpoint,
)

router = routers.DefaultRouter(trailing_slash=False)

urlpatterns = [
    path("", include(router.urls)),
    # Dashboard
    path(
        "workspaces/<str:slug>/dashboard",
        DashboardEndpoint.as_view(),
        name="dashboard",
    ),
    path(
        "workspaces/<str:slug>/dashboard/<int:dashboard_id>",
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
        "workspaces/<str:slug>/analytics/export",
        ExportAnalyticsEndpoint.as_view(),
        name="export-analytics",
    ),
    path(
        "workspaces/<str:slug>/analytics",
        AnalyticsEndpoint.as_view(),
        name="servcy-analytics",
    ),
    path(
        "workspaces/<str:slug>/analytics/view",
        AnalyticViewViewset.as_view({"get": "list", "post": "create"}),
        name="analytic-view",
    ),
    path(
        "workspaces/<str:slug>/analytics/default",
        DefaultAnalyticsEndpoint.as_view(),
        name="default-analytics",
    ),
]
