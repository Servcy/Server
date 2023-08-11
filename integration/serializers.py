from app.serializers import ServcyReadSerializer
from integration.models import Integration


class IntegrationSerializer(ServcyReadSerializer):
    class Meta:
        model = Integration
        fields = "__all__"
