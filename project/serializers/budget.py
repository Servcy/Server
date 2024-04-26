from app.serializers import ServcyBaseSerializer
from project.models import ProjectBudget, ProjectExpense, ProjectMemberRate


class ProjectBudgetSerializer(ServcyBaseSerializer):
    class Meta:
        model = ProjectBudget
        fields = "__all__"


class ProjectMemberRateSerializer(ServcyBaseSerializer):
    class Meta:
        model = ProjectMemberRate
        fields = "__all__"


class ProjectExpenseSerializer(ServcyBaseSerializer):
    class Meta:
        model = ProjectExpense
        fields = "__all__"
