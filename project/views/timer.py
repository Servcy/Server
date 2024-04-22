from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.db.models import Q
from common.permissions import ProjectMemberPermission
from common.responses import error_response
from iam.enums import ERole
from common.views import BaseViewSet
from project.models import Issue, TrackedTime, TrackedTimeAttachment
from iam.models import WorkspaceMember
from project.serializers import TrackedTimeAttachmentSerializer, TrackedTimeSerializer


class TrackedTimeViewSet(BaseViewSet):
    """
    TrackedTimeViewSet (viewset): To handle all the tracked time related operations
    """

    permission_classes = [ProjectMemberPermission]
    serializer_class = TrackedTimeSerializer
    queryset = TrackedTime.objects.all()

    def create(self, request, workspace_slug, project_id, issue_id, *args, **kwargs):
        """
        create (method): To create a new tracked time record
        """
        if TrackedTime.objects.filter(
            workspace__slug=workspace_slug,
            created_by=request.user,
            end_time__isnull=True,
        ).exists():
            return error_response("Timer is already running for this user", status=400)
        try:
            issue = Issue.objects.get(
                archived_at__isnull=True,
                is_draft=False,
                id=issue_id,
                project_id=project_id,
                workspace__slug=workspace_slug,
            )
        except Issue.DoesNotExist:
            raise PermissionDenied("Issue not found")
        tracked_time = TrackedTime.objects.create(
            description=request.data.get("description", ""),
            is_billable=request.data.get("is_billable", True),
            issue_id=issue_id,
            project_id=project_id,
            workspace=issue.workspace,
            created_by=request.user,
            updated_by=request.user,
            start_time=timezone.now(),
            end_time=None,
            is_approved=False,
        )
        return Response(
            TrackedTimeSerializer(tracked_time).data,
            status=201,
        )

    def list(self, request, workspace_slug, *args, **kwargs):
        """
        list (method): To list all the tracked time records
        """
        isWorkspaceAdmin = WorkspaceMember.objects.filter(
            workspace__slug=workspace_slug,
            member=request.user,
            is_active=True,
            role__gte=ERole.ADMIN.value,
        ).exists()
        project_id = request.query_params.get("project_id")
        issue_id = request.query_params.get("issue_id")
        query = Q(
            workspace__slug=workspace_slug,
            end_time__isnull=False,
        )
        if project_id:
            query = query & Q(project_id=int(project_id))
        if issue_id:
            query = query & Q(issue_id=int(issue_id))
        if not isWorkspaceAdmin:
            query = query & Q(created_by=request.user)
        timeEntries = TrackedTime.objects.filter(query).order_by("-start_time")
        return Response(
            TrackedTimeSerializer(timeEntries, many=True).data,
            status=200,
        )

    def stop_timer(
        self, request, workspace_slug, project_id, timer_id, *args, **kwargs
    ):
        """
        stop_timer (method): To stop the running timer
        """
        try:
            tracked_time = TrackedTime.objects.get(
                workspace__slug=workspace_slug,
                id=timer_id,
                created_by=request.user,
                project_id=project_id,
                end_time__isnull=True,
            )
        except TrackedTime.DoesNotExist:
            raise PermissionDenied("Timer not found")
        tracked_time.end_time = timezone.now()
        tracked_time.save()
        return Response(
            TrackedTimeSerializer(tracked_time).data,
            status=200,
        )

    def is_timer_running(self, request, workspace_slug, *args, **kwargs):
        """
        is_timer_running (method): To check if the timer is running for the user
        """
        isTimerRunning = TrackedTime.objects.filter(
            workspace__slug=workspace_slug,
            created_by=request.user,
            end_time__isnull=True,
        ).exists()
        return Response(
            isTimerRunning,
            status=200,
        )


class TrackedTimeAttachmentViewSet(BaseViewSet):
    """
    TrackedTimeAttachmentViewSet (viewset): To handle all the tracked time attachment related operations
    """

    serializer_class = TrackedTimeAttachmentSerializer
    queryset = TrackedTimeAttachment.objects.all()
