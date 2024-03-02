from django.db.models import Case, Exists, F, JSONField, OuterRef, Subquery, When
from rest_framework import status

from common.responses import Response, error_response
from common.views import BaseAPIView
from dashboard.models import Dashboard, DashboardWidget, Widget
from dashboard.serializers import DashboardSerializer, WidgetSerializer
from dashboard.utils import (
    dashboard_assigned_issues,
    dashboard_created_issues,
    dashboard_issues_by_priority,
    dashboard_issues_by_state_groups,
    dashboard_overview_stats,
    dashboard_recent_activity,
    dashboard_recent_collaborators,
    dashboard_recent_projects,
)


class DashboardEndpoint(BaseAPIView):
    def create(self, request, **kwargs):
        serializer = DashboardSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, **kwargs):
        serializer = DashboardSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, **kwargs):
        serializer = DashboardSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, workspace_id, dashboard_id=None):
        """
        Get the dashboard details
        - If dashboard_id is not provided, then it will return the default dashboard
        """
        if not dashboard_id:
            dashboard_type = request.GET.get("dashboard_type", None)
            if dashboard_type == "home":
                dashboard, created = Dashboard.objects.get_or_create(
                    type_identifier=dashboard_type,
                    owned_by=request.user,
                    is_default=True,
                )

                if created:
                    widgets_to_fetch = [
                        "overview_stats",
                        "assigned_issues",
                        "created_issues",
                        "issues_by_state_groups",
                        "issues_by_priority",
                        "recent_activity",
                        "recent_projects",
                        "recent_collaborators",
                    ]

                    updated_dashboard_widgets = []
                    for widget_key in widgets_to_fetch:
                        widget = Widget.objects.filter(key=widget_key).values_list(
                            "id", flat=True
                        )
                        if widget:
                            updated_dashboard_widgets.append(
                                DashboardWidget(
                                    widget_id=widget,
                                    dashboard_id=dashboard.id,
                                )
                            )

                    DashboardWidget.objects.bulk_create(
                        updated_dashboard_widgets, batch_size=100
                    )

                widgets = (
                    Widget.objects.annotate(
                        is_visible=Exists(
                            DashboardWidget.objects.filter(
                                widget_id=OuterRef("pk"),
                                dashboard_id=dashboard.id,
                                is_visible=True,
                            )
                        )
                    )
                    .annotate(
                        dashboard_filters=Subquery(
                            DashboardWidget.objects.filter(
                                widget_id=OuterRef("pk"),
                                dashboard_id=dashboard.id,
                                filters__isnull=False,
                            )
                            .exclude(filters={})
                            .values("filters")[:1]
                        )
                    )
                    .annotate(
                        widget_filters=Case(
                            When(
                                dashboard_filters__isnull=False,
                                then=F("dashboard_filters"),
                            ),
                            default=F("filters"),
                            output_field=JSONField(),
                        )
                    )
                )
                return Response(
                    {
                        "dashboard": DashboardSerializer(dashboard).data,
                        "widgets": WidgetSerializer(widgets, many=True).data,
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"error": "Please specify a valid dashboard type"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        widget_key = request.GET.get("widget_key", "overview_stats")
        WIDGETS_MAPPER = {
            "overview_stats": dashboard_overview_stats,
            "assigned_issues": dashboard_assigned_issues,
            "created_issues": dashboard_created_issues,
            "issues_by_state_groups": dashboard_issues_by_state_groups,
            "issues_by_priority": dashboard_issues_by_priority,
            "recent_activity": dashboard_recent_activity,
            "recent_projects": dashboard_recent_projects,
            "recent_collaborators": dashboard_recent_collaborators,
        }
        func = WIDGETS_MAPPER.get(widget_key)
        if func is not None:
            response = func(
                self,
                request=request,
                workspace_id=workspace_id,
            )
            if isinstance(response, Response):
                return response
        return error_response(
            "Please specify a valid widget key",
            status=status.HTTP_400_BAD_REQUEST,
        )


class WidgetsEndpoint(BaseAPIView):
    def patch(self, request, dashboard_id, widget_id):
        dashboard_widget = DashboardWidget.objects.filter(
            widget_id=widget_id,
            dashboard_id=dashboard_id,
        ).first()
        dashboard_widget.is_visible = request.data.get(
            "is_visible", dashboard_widget.is_visible
        )
        dashboard_widget.sort_order = request.data.get(
            "sort_order", dashboard_widget.sort_order
        )
        dashboard_widget.filters = request.data.get("filters", dashboard_widget.filters)
        dashboard_widget.save()
        return Response({"message": "successfully updated"}, status=status.HTTP_200_OK)
