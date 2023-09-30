from app.serializers import ServcyReadSerializer
from inbox.models import Inbox


class InboxSerializer(ServcyReadSerializer):
    class Meta:
        model = Inbox
        fields = "__all__"
