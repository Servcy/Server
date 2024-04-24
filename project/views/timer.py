from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from common.permissions import ProjectMemberPermission
from common.responses import error_response
from common.views import BaseViewSet
from iam.enums import ERole
from iam.models import WorkspaceMember
from project.models import Issue, TrackedTime, TrackedTimeAttachment
from project.serializers import TrackedTimeAttachmentSerializer, TrackedTimeSerializer
from project.utils.filters import timesheet_filters


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
        running_timer_exists = Q(
            workspace__slug=workspace_slug,
            created_by=request.user,
            end_time__isnull=True,
        )
        if TrackedTime.objects.filter(running_timer_exists).exists():
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
        end_time = request.data.get("end_time", None)
        is_manually_added = False
        if end_time:
            is_manually_added = True
            end_time = timezone.make_aware(
                timezone.datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.%fZ")
            )
            if end_time < timezone.now():
                return error_response("End time cannot be in the past", status=400)
            # if log is less than 5 minutes, then it will be discarded
            if (end_time - timezone.now()).seconds < 300:
                return error_response(
                    "Time log should be greater than 5 minutes", status=400
                )
        tracked_time = TrackedTime.objects.create(
            description=request.data.get("description", ""),
            is_billable=request.data.get("is_billable", True),
            issue_id=issue_id,
            project_id=project_id,
            workspace=issue.workspace,
            is_manually_added=is_manually_added,
            created_by=request.user,
            updated_by=request.user,
            start_time=timezone.now(),
            end_time=end_time,
            is_approved=False,
        )
        return Response(
            TrackedTimeSerializer(tracked_time).data,
            status=201,
        )

    def list(self, request, workspace_slug, viewId, *args, **kwargs):
        """
        list (method): To list all the tracked time records
        """
        isWorkspaceAdmin = WorkspaceMember.objects.filter(
            workspace__slug=workspace_slug,
            member=request.user,
            is_active=True,
            role__gte=ERole.ADMIN.value,
        ).exists()
        filters = timesheet_filters(request.query_params, "GET")
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
            if viewId == "workspace-timesheet":
                raise PermissionDenied(
                    "You are not allowed to view workspace timesheet"
                )
            query = query & Q(created_by=request.user)
        timesheet = (
            TrackedTime.objects.filter(query).filter(**filters).order_by("-start_time")
        )
        return Response(
            TrackedTimeSerializer(timesheet, many=True).data,
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
        end_time = timezone.now()
        if (end_time - tracked_time.start_time).seconds < 300:
            tracked_time.delete()
            return Response(status=204)
        tracked_time.end_time = end_time
        tracked_time.save()
        return Response(
            TrackedTimeSerializer(tracked_time).data,
            status=200,
        )

    def is_timer_running(self, request, workspace_slug, *args, **kwargs):
        """
        is_timer_running (method): To check if the timer is running for the user
        """
        timerRunning = TrackedTime.objects.get(
            workspace__slug=workspace_slug,
            created_by=request.user,
            end_time__isnull=True,
        )
        return Response(
            TrackedTimeSerializer(timerRunning).data,
            status=200,
        )

    def delete(self, request, workspace_slug, project_id, time_log_id, *args, **kwargs):
        """
        delete (method): To delete a tracked time record
        """
        try:
            tracked_time = TrackedTime.objects.get(
                workspace__slug=workspace_slug,
                id=time_log_id,
                created_by=request.user,
                end_time__isnull=False,
            )
        except TrackedTime.DoesNotExist:
            raise PermissionDenied("Timer not found")
        tracked_time.delete()
        return Response(status=204)

    def update(self, request, workspace_slug, project_id, time_log_id, *args, **kwargs):
        """
        update (method): To update a tracked time record
        """
        try:
            tracked_time = TrackedTime.objects.get(
                workspace__slug=workspace_slug,
                id=time_log_id,
                created_by=request.user,
                is_approved=False,
                end_time__isnull=False,
            )
        except TrackedTime.DoesNotExist:
            raise PermissionDenied("Timer not found")
        end_time = request.data.get("end_time", None)
        if end_time:
            end_time = timezone.make_aware(
                timezone.datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.%fZ")
            )
            if end_time < timezone.now():
                return error_response("End time cannot be in the past", status=400)
            # if log is less than 5 minutes, then it will be discarded
            if (end_time - timezone.now()).seconds < 300:
                return error_response(
                    "Time log should be greater than 5 minutes", status=400
                )
        tracked_time.description = request.data.get("description", "")
        tracked_time.is_billable = request.data.get("is_billable", True)
        tracked_time.is_manually_added = True
        tracked_time.end_time = end_time
        tracked_time.updated_by = request.user
        tracked_time.save()
        return Response(
            TrackedTimeSerializer(tracked_time).data,
            status=200,
        )


class TrackedTimeAttachmentViewSet(BaseViewSet):
    """
    TrackedTimeAttachmentViewSet (viewset): To handle all the tracked time attachment related operations
    """

    serializer_class = TrackedTimeAttachmentSerializer
    model = TrackedTimeAttachment
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, tracked_time_id):
        snapshots = TrackedTimeAttachment.objects.filter(
            tracked_time_id=tracked_time_id, created_by=request.user
        )
        serializer = TrackedTimeAttachmentSerializer(snapshots, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, tracked_time_id):
        tracked_time = TrackedTime.objects.get(
            id=tracked_time_id, created_by=request.user
        )
        snapshot = request.data
        snapshot["project"] = tracked_time.project_id
        snapshot["workspace"] = tracked_time.workspace_id
        serializer = TrackedTimeAttachmentSerializer(data=snapshot, partial=True)
        if serializer.is_valid():
            serializer.save(
                tracked_time_id=tracked_time.id,
                created_by=self.request.user,
                updated_by=self.request.user,
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, tracked_time_id, pk):
        snapshot = TrackedTimeAttachment.objects.get(
            pk=pk, created_by=request.user, tracked_time_id=tracked_time_id
        )
        snapshot.file.delete(save=False)
        snapshot.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
