from rest_framework.serializers import ModelSerializer

from project.models import Project


class ProjectSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "file_ids",
            "created_at",
            "updated_at",
            "uid",
            "meta_data",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
