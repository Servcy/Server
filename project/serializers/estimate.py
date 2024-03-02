from rest_framework import serializers

from app.serializers import ServcyBaseSerializer
from iam.serializers import WorkspaceLiteSerializer
from project.models import Estimate, EstimatePoint

from .project import ProjectLiteSerializer


class EstimateSerializer(ServcyBaseSerializer):
    workspace_detail = WorkspaceLiteSerializer(read_only=True, source="workspace")
    project_detail = ProjectLiteSerializer(read_only=True, source="project")

    class Meta:
        model = Estimate
        fields = "__all__"
        read_only_fields = [
            "workspace",
            "project",
        ]


class EstimatePointSerializer(ServcyBaseSerializer):
    def validate(self, data):
        if not data:
            raise serializers.ValidationError("Estimate points are required")
        value = data.get("value")
        if value and len(value) > 20:
            raise serializers.ValidationError("Value can't be more than 20 characters")
        return data

    class Meta:
        model = EstimatePoint
        fields = "__all__"
        read_only_fields = [
            "estimate",
            "workspace",
            "project",
        ]


class EstimateReadSerializer(ServcyBaseSerializer):
    points = EstimatePointSerializer(read_only=True, many=True)
    workspace_detail = WorkspaceLiteSerializer(read_only=True, source="workspace")
    project_detail = ProjectLiteSerializer(read_only=True, source="project")

    class Meta:
        model = Estimate
        fields = "__all__"
        read_only_fields = [
            "points",
            "name",
            "description",
        ]


class EstimatePointReadSerializer(ServcyBaseSerializer):
    points = EstimatePointSerializer(read_only=True, many=True)

    class Meta:
        model = Estimate
        fields = "__all__"
        read_only_fields = [
            "points",
            "name",
            "description",
        ]
