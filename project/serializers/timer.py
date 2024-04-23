from app.serializers import ServcyBaseSerializer
from rest_framework import serializers
from project.models import TrackedTime, TrackedTimeAttachment
from project.serializers import IssueUltraLiteSerializer, ProjectUltraLiteSerializer


class TrackedTimeSerializer(ServcyBaseSerializer):
    issue_detail = IssueUltraLiteSerializer(read_only=True, source="issue")
    project_detail = ProjectUltraLiteSerializer(read_only=True, source="project")
    snapshots = serializers.SerializerMethodField()

    def get_snapshots(self, obj):
        snapshots = TrackedTimeAttachment.objects.filter(tracked_time=obj)
        return TrackedTimeAttachmentSerializer(snapshots, many=True).data

    class Meta:
        model = TrackedTime
        fields = "__all__"


class TrackedTimeAttachmentSerializer(ServcyBaseSerializer):
    tracked_time = TrackedTimeSerializer(read_only=True)

    class Meta:
        model = TrackedTimeAttachment
        fields = "__all__"
