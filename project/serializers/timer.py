from app.serializers import ServcyBaseSerializer
from project.models import TrackedTime, TrackedTimeAttachment


class TrackedTimeSerializer(ServcyBaseSerializer):
    class Meta:
        model = TrackedTime
        fields = "__all__"


class TrackedTimeAttachmentSerializer(ServcyBaseSerializer):
    class Meta:
        model = TrackedTimeAttachment
        fields = "__all__"
