from itertools import groupby

from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response

from common.permissions import ProjectEntityPermission
from common.views import BaseViewSet
from project.models import Issue, State
from project.serializers import StateSerializer


class StateViewSet(BaseViewSet):
    serializer_class = StateSerializer
    model = State
    permission_classes = [
        ProjectEntityPermission,
    ]

    def get_queryset(self):
        return self.filter_queryset(
            super()
            .get_queryset()
            .filter(workspace__slug=self.kwargs.get("workspace_slug"))
            .filter(project_id=self.kwargs.get("project_id"))
            .filter(
                project__project_projectmember__member=self.request.user,
                project__archived_at__isnull=True,
                project__project_projectmember__is_active=True,
            )
            .filter(~Q(name="Triage"))
            .select_related("project")
            .select_related("workspace")
            .distinct()
        )

    def create(self, request, workspace_slug, project_id):
        serializer = StateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                project_id=project_id, created_by=request.user, updated_by=request.user
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, **kwargs):
        states = StateSerializer(self.get_queryset(), many=True).data
        grouped = request.GET.get("grouped", False)
        if grouped == "true":
            state_dict = {}
            for key, value in groupby(
                sorted(states, key=lambda state: state["group"]),
                lambda state: state.get("group"),
            ):
                state_dict[str(key)] = list(value)
            return Response(state_dict, status=status.HTTP_200_OK)
        return Response(states, status=status.HTTP_200_OK)

    def mark_as_default(self, request, workspace_slug, project_id, pk):
        # Select all the states which are marked as default
        _ = State.objects.filter(
            workspace__slug=workspace_slug, project_id=project_id, default=True
        ).update(default=False)
        _ = State.objects.filter(
            workspace__slug=workspace_slug, project_id=project_id, pk=pk
        ).update(default=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, workspace_slug, project_id, pk):
        state = State.objects.get(
            ~Q(name="Triage"),
            pk=pk,
            project_id=project_id,
            workspace__slug=workspace_slug,
        )

        if state.default:
            return Response(
                {"error": "Default state cannot be deleted"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check for any issues in the state
        issue_exist = Issue.issue_objects.filter(state=pk).exists()

        if issue_exist:
            return Response(
                {"error": "The state is not empty, only empty states can be deleted"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        state.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
