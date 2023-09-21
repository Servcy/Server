from rest_framework.serializers import ModelSerializer

from project.models import Project


class ProjectSerializer(ModelSerializer):
    class Meta:
        model = Project
        read_only_fields = (
            "id",
            "account_display_name",
        )
        fields = read_only_fields + ("configuration",)
