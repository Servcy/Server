from common.permissions import WorkSpaceAdminPermission
from common.responses import error_response
from rest_framework.response import Response
from common.views import BaseViewSet
from project.models import ProjectExpense, Project
from project.serializers import ProjectExpenseSerializer


class ProjectExpenseViewSet(BaseViewSet):
    """
    Project Expense ViewSet: To handle all the CRUD operations of the project expenses
    """

    model = ProjectExpense
    permission_classes = [WorkSpaceAdminPermission]
    serializer_class = ProjectExpenseSerializer

    def list(self, request, workspace_slug, project_id):
        expenses = ProjectExpense.objects.filter(
            project_id=project_id, workspace__slug=workspace_slug
        )
        serializer = self.serializer_class(expenses, many=True)
        return Response(serializer.data, status=200)

    def destroy(self, request, workspace_slug, project_id):
        data = request.data
        expense_id = data.get("expense_id")
        if not expense_id:
            return error_response("expense_id is required", status=400)
        expense = ProjectExpense.objects.filter(
            id=expense_id, project_id=project_id, workspace__slug=workspace_slug
        ).first()
        if not expense:
            return error_response("Expense not found", status=404)
        expense.delete()
        return Response(status=204)

    def partial_update(self, request, workspace_slug, project_id):
        data = request.data
        expense_id = data.get("expense_id")
        if not expense_id:
            return error_response("expense_id is required", status=400)
        expense = ProjectExpense.objects.filter(
            id=expense_id, project_id=project_id, workspace__slug=workspace_slug
        ).first()
        if not expense:
            return error_response("Expense not found", status=404)
        serializer = self.serializer_class(expense, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return error_response(serializer.errors, status=400)

    def create(self, request, workspace_slug, project_id):
        data = request.data
        project = Project.objects.filter(
            id=project_id, workspace__slug=workspace_slug, archived_at__isnull=True
        ).first()
        if not project:
            return error_response("Project not found", status=404)
        data["project"] = project.id
        data["workspace"] = project.workspace_id
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return error_response(serializer.errors, status=400)
