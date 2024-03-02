from rest_framework import serializers

from app.serializers import ServcyBaseSerializer
from project.models import Cycle, CycleFavorite, CycleIssue, CycleUserProperties

from .issue import IssueStateSerializer


class CycleWriteSerializer(ServcyBaseSerializer):
    def validate(self, data):
        if (
            data.get("start_date", None) is not None
            and data.get("end_date", None) is not None
            and data.get("start_date", None) > data.get("end_date", None)
        ):
            raise serializers.ValidationError("Start date cannot exceed end date")
        return data

    class Meta:
        model = Cycle
        fields = "__all__"
        read_only_fields = [
            "workspace",
            "project",
            "owned_by",
        ]


class CycleSerializer(ServcyBaseSerializer):
    # favorite
    is_favorite = serializers.BooleanField(read_only=True)
    total_issues = serializers.IntegerField(read_only=True)
    # state group wise distribution
    cancelled_issues = serializers.IntegerField(read_only=True)
    completed_issues = serializers.IntegerField(read_only=True)
    started_issues = serializers.IntegerField(read_only=True)
    unstarted_issues = serializers.IntegerField(read_only=True)
    backlog_issues = serializers.IntegerField(read_only=True)

    # active | draft | upcoming | completed
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Cycle
        fields = [
            # necessary fields
            "id",
            "workspace_id",
            "project_id",
            # model fields
            "name",
            "description",
            "start_date",
            "end_date",
            "owned_by_id",
            "view_props",
            "sort_order",
            "external_source",
            "external_id",
            "progress_snapshot",
            # meta fields
            "is_favorite",
            "total_issues",
            "cancelled_issues",
            "completed_issues",
            "started_issues",
            "unstarted_issues",
            "backlog_issues",
            "status",
        ]
        read_only_fields = fields


class CycleIssueSerializer(ServcyBaseSerializer):
    issue_detail = IssueStateSerializer(read_only=True, source="issue")
    sub_issues_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = CycleIssue
        fields = "__all__"
        read_only_fields = [
            "workspace",
            "project",
            "cycle",
        ]


class CycleFavoriteSerializer(ServcyBaseSerializer):
    cycle_detail = CycleSerializer(source="cycle", read_only=True)

    class Meta:
        model = CycleFavorite
        fields = "__all__"
        read_only_fields = [
            "workspace",
            "project",
            "user",
        ]


class CycleUserPropertiesSerializer(ServcyBaseSerializer):
    class Meta:
        model = CycleUserProperties
        fields = "__all__"
        read_only_fields = [
            "workspace",
            "project",
            "cycle" "user",
        ]
