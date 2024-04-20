from app.serializers import ServcyBaseSerializer
from project.models import ProjectBudget, ProjectMemberRate


class ProjectBudgetSerializer(ServcyBaseSerializer):
    class Meta:
        model = ProjectBudget
        fields = "__all__"


class ProjectMemberRateSerializer(ServcyBaseSerializer):
    class Meta:
        model = ProjectMemberRate
        fields = "__all__"
