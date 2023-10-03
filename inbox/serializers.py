from app.serializers import ServcyReadSerializer
from inbox.models import Inbox
from serpy import MethodField


class InboxSerializer(ServcyReadSerializer):
    source = MethodField()

    def get_source(self, obj):
        return obj.user_integration.integration.name

    class Meta:
        model = Inbox
        fields = "__all__"
