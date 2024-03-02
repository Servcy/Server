from rest_framework import serializers

from app.serializers import ServcyBaseSerializer
from dashboard.models import Analytic, Dashboard, Widget
from project.utils.filters import issue_filters


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


class AnalyticSerializer(ServcyBaseSerializer):
    class Meta:
        model = Analytic
        fields = "__all__"
        read_only_fields = [
            "workspace",
            "query",
        ]

    def create(self, validated_data):
        query_params = validated_data.get("query_dict", {})
        if bool(query_params):
            validated_data["query"] = issue_filters(query_params, "POST")
        else:
            validated_data["query"] = {}
        return Analytic.objects.create(**validated_data)

    def update(self, instance, validated_data):
        query_params = validated_data.get("query_data", {})
        if bool(query_params):
            validated_data["query"] = issue_filters(query_params, "POST")
        else:
            validated_data["query"] = {}
        validated_data["query"] = issue_filters(query_params, "PATCH")
        return super().update(instance, validated_data)
