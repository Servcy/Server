from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField

from client.models import Client, Avatar


class ClientSerializer(ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "user"]
