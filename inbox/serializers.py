from serpy import MethodField

from app.serializers import ServcyReadSerializer
from inbox.models import Inbox


class InboxSerializer(ServcyReadSerializer):
    source = MethodField()
    account = MethodField()

    def get_source(self, obj):
        return obj.user_integration.integration.name

    def get_account(self, obj):
        return obj.user_integration.account_display_name

    class Meta:
        model = Inbox
        fields = "__all__"
