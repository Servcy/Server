from serpy import MethodField

from app.serializers import ServcyReadSerializer
from integration.models import Integration


class IntegrationSerializer(ServcyReadSerializer):
    account_display_names = MethodField()

    class Meta:
        model = Integration
        fields = (
            "id",
            "name",
            "description",
            "logo",
            "account_display_name",
            "account_id",
        )

    def get_account_display_names(self, obj):
        user_integrations = obj.user_integrations.all()
        return [
            user_integration.account_display_name
            for user_integration in user_integrations
        ]
