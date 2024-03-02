from rest_framework import serializers

from app.serializers import ServcyBaseSerializer
from dashboard.models import Dashboard, Widget


class DashboardSerializer(ServcyBaseSerializer):
    class Meta:
        model = Dashboard
        fields = "__all__"


class WidgetSerializer(ServcyBaseSerializer):
    is_visible = serializers.BooleanField(read_only=True)
    widget_filters = serializers.JSONField(read_only=True)

    class Meta:
        model = Widget
        fields = ["id", "key", "is_visible", "widget_filters"]
