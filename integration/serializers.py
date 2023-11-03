from rest_framework.serializers import ModelSerializer
from serpy import MethodField

from app.serializers import ServcyReadSerializer
from integration.models import Integration, UserIntegration


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
            "is_wip",
            "configure_at",
        )

    def get_account_display_names(self, obj):
        user_integrations = obj.user_integrations.filter(is_revoked=False).all()
        return [
            user_integration.account_display_name
            for user_integration in user_integrations
        ]


class UserIntegrationSerializer(ModelSerializer):
    class Meta:
        model = UserIntegration
        read_only_fields = (
            "id",
            "account_display_name",
        )
        fields = read_only_fields + ("configuration",)
