from serpy import MethodField

from app.serializers import ServcyReadSerializer
from inbox.models import Inbox


class InboxSerializer(ServcyReadSerializer):
    source = MethodField()

    def get_source(self, obj):
        return obj.user_integration.integration.name

    class Meta:
        model = Inbox
        fields = "__all__"
