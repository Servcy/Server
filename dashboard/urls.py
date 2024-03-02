from django.urls import include, path
from rest_framework import routers

from dashboard.views import DashboardEndpoint, WidgetsEndpoint

router = routers.DefaultRouter(trailing_slash=False)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "workspaces/<int:workspace_id>/dashboard/",
        DashboardEndpoint.as_view(),
        name="dashboard",
    ),
    path(
        "workspaces/<int:workspace_id>/dashboard/<int:dashboard_id>/",
        DashboardEndpoint.as_view(),
        name="dashboard",
    ),
    path(
        "dashboard/<int:dashboard_id>/widgets/<int:widget_id>/",
        WidgetsEndpoint.as_view(),
        name="widgets",
    ),
]
