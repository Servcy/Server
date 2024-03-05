from app.serializers import ServcyBaseSerializer
from iam.serializers import UserLiteSerializer
from notification.models import Notification, UserNotificationPreference


class UserNotificationPreferenceSerializer(ServcyBaseSerializer):
    class Meta:
        model = UserNotificationPreference
        fields = "__all__"


class NotificationSerializer(ServcyBaseSerializer):
    triggered_by_details = UserLiteSerializer(read_only=True, source="triggered_by")

    class Meta:
        model = Notification
        fields = "__all__"
