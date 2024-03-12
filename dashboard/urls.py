from django.urls import include, path
from rest_framework import routers

from dashboard.views import (
    AnalyticsEndpoint,
    AnalyticViewViewset,
    DashboardEndpoint,
    DefaultAnalyticsEndpoint,
    ExportAnalyticsEndpoint,
    SavedAnalyticEndpoint,
    WidgetsEndpoint,
)

router = routers.DefaultRouter(trailing_slash=False)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "workspaces/<str:slug>/dashboard/",
        DashboardEndpoint.as_view(),
        name="dashboard",
    ),
    path(
        "workspaces/<str:slug>/dashboard/<int:dashboard_id>/",
        DashboardEndpoint.as_view(),
        name="dashboard",
    ),
    path(
        "dashboard/<int:dashboard_id>/widgets/<int:widget_id>/",
        WidgetsEndpoint.as_view(),
        name="widgets",
    ),
    path(
        "workspaces/<str:slug>/export-analytics/",
        ExportAnalyticsEndpoint.as_view(),
        name="export-analytics",
    ),
    path(
        "workspaces/<str:slug>/analytics/",
        AnalyticsEndpoint.as_view(),
        name="servcy-analytics",
    ),
    path(
        "workspaces/<str:slug>/analytic-view/",
        AnalyticViewViewset.as_view({"get": "list", "post": "create"}),
        name="analytic-view",
    ),
    path(
        "workspaces/<str:slug>/analytic-view/<int:pk>/",
        AnalyticViewViewset.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="analytic-view",
    ),
    path(
        "workspaces/<str:slug>/saved-analytic-view/<int:analytic_id>/",
        SavedAnalyticEndpoint.as_view(),
        name="saved-analytic-view",
    ),
    path(
        "workspaces/<str:slug>/default-analytics/",
        DefaultAnalyticsEndpoint.as_view(),
        name="default-analytics",
    ),
]
