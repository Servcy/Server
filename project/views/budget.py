from common.permissions import WorkSpaceAdminPermission
from common.views import BaseViewSet
from project.models import ProjectExpense
from project.serializers import ProjectExpenseSerializer


class ProjectExpenseViewSet(BaseViewSet):
    """
    Project Expense ViewSet: To handle all the CRUD operations of the project expenses
    """

    model = ProjectExpense
    permission_classes = [WorkSpaceAdminPermission]
    serializer_class = ProjectExpenseSerializer

    def list(self, request, workspace_slug, project_id):
        pass

    def destroy(self, request, workspace_slug, project_id):
        pass

    def partial_update(self, request, workspace_slug, project_id):
        pass

    def create(self, request, workspace_slug, project_id):
        pass
