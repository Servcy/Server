from rest_framework.serializers import ModelSerializer
from serpy import MethodField

from app.serializers import ServcyReadSerializer
from integration.models import Integration, UserIntegration


class IntegrationSerializer(ServcyReadSerializer):
    is_connected = MethodField()

    class Meta:
        model = Integration
        fields = (
            "id",
            "name",
            "description",
            "logo",
            "account_id",
            "is_wip",
            "configure_at",
        )

    def get_is_connected(self, obj):
        return obj.user_integrations.filter(is_revoked=False).exists()


class UserIntegrationSerializer(ModelSerializer):
    class Meta:
        model = UserIntegration
        read_only_fields = (
            "id",
            "account_display_name",
        )
        fields = read_only_fields + ("configuration",)
