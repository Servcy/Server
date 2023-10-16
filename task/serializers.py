from rest_framework.serializers import ModelSerializer

from task.models import Task


class TaskSerializer(ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "name",
            "description",
            "file_ids",
            "meta_data",
            "project_uid",
            "created_at",
            "updated_at",
            "uid",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
