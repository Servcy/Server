from app.serializers import ServcyReadSerializer
from billing.models import Subscription


class SubscriptionSerializer(ServcyReadSerializer):
    class Meta:
        model = Subscription
        fields = "__all__"
