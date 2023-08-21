from serpy import MethodField

from app.serializers import ServcyReadSerializer
from integration.models import Integration, IntegrationUser


class IntegrationSerializer(ServcyReadSerializer):
    account_ids = MethodField()

    class Meta:
        model = Integration
        fields = (
            "id",
            "name",
            "description",
            "logo",
            "account_id",
        )

    def get_account_ids(self, obj):
        integration_user = obj.integration_users.all()
        return [integration.account_id for integration in integration_user]


class IntegrationUserSerializer(ServcyReadSerializer):
    class Meta:
        model = IntegrationUser
        fields = ["account_id", "user", "integration"]
