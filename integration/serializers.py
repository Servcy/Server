from rest_framework.serializers import ModelSerializer

from integration.models import UserIntegration


class UserIntegrationSerializer(ModelSerializer):
    class Meta:
        model = UserIntegration
        read_only_fields = (
            "id",
            "account_display_name",
        )
        fields = read_only_fields + ("configuration",)
