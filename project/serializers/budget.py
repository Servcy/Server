from app.serializers import ServcyBaseSerializer
from project.models import Budget, ProjectMemberRate


class BudgetSerializer(ServcyBaseSerializer):
    class Meta:
        model = Budget
        fields = "__all__"


class ProjectMemberRateSerializer(ServcyBaseSerializer):
    class Meta:
        model = ProjectMemberRate
        fields = "__all__"
