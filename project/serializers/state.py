from app.serializers import ServcyBaseSerializer
from project.models import State


class StateSerializer(ServcyBaseSerializer):
    class Meta:
        model = State
        fields = [
            "id",
            "project_id",
            "workspace_id",
            "name",
            "color",
            "group",
            "default",
            "description",
            "sequence",
        ]
        read_only_fields = [
            "workspace",
            "project",
        ]


class StateLiteSerializer(ServcyBaseSerializer):
    class Meta:
        model = State
        fields = [
            "id",
            "name",
            "color",
            "group",
        ]
        read_only_fields = fields
