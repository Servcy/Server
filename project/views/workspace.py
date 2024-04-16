import logging
from datetime import date

from dateutil.relativedelta import relativedelta
from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.postgres.fields import ArrayField
from django.db.models import (
    BigIntegerField,
    Case,
    CharField,
    Count,
    F,
    Func,
    IntegerField,
    Max,
    OuterRef,
    Prefetch,
    Q,
    Sum,
    Value,
    When,
)
from django.db.models.fields import DateField
from django.db.models.functions import Cast, Coalesce, ExtractDay, ExtractWeek
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from common.paginator import BasePaginator
from common.permissions import WorkspaceEntityPermission, WorkspaceUserPermission
from common.views import BaseAPIView
from iam.enums import ERole
from iam.models import User, Workspace, WorkspaceMember
from iam.serializers import WorkSpaceSerializer
from project.models import (
    Cycle,
    CycleIssue,
    Estimate,
    EstimatePoint,
    Issue,
    IssueActivity,
    IssueAttachment,
    IssueLink,
    IssueSubscriber,
    Label,
    Module,
    ModuleLink,
    Project,
    State,
)
from project.serializers import (
    CycleSerializer,
    EstimatePointReadSerializer,
    IssueActivitySerializer,
    IssueSerializer,
    LabelSerializer,
    ModuleSerializer,
    StateSerializer,
)
from project.utils.filters import issue_filters

logger = logging.getLogger(__name__)


class UserWorkSpacesEndpoint(BaseAPIView):
    """
    This endpoint returns the workspaces of the user
    - The user can be a member of multiple workspaces
    - The user can be an owner of multiple workspaces
    """

    search_fields = [
        "name",
    ]
    filterset_fields = [
        "owner",
    ]

    def get(self, request):
        fields = [field for field in request.GET.get("fields", "").split(",") if field]
        member_count = (
            WorkspaceMember.objects.filter(
                workspace=OuterRef("id"),
                is_active=True,
            )
            .order_by()
            .annotate(count=Func(F("id"), function="Count"))
            .values("count")
        )

        issue_count = (
            Issue.issue_objects.filter(workspace=OuterRef("id"))
            .order_by()
            .annotate(count=Func(F("id"), function="Count"))
            .values("count")
        )
        workspace = (
            Workspace.objects.prefetch_related(
                Prefetch(
                    "workspace_member",
                    queryset=WorkspaceMember.objects.filter(
                        member=request.user, is_active=True
                    ),
                )
            )
            .select_related("owner")
            .annotate(total_members=member_count)
            .annotate(total_issues=issue_count)
            .filter(
                workspace_member__member=request.user,
                workspace_member__is_active=True,
            )
            .distinct()
        )
        workspaces = WorkSpaceSerializer(
            self.filter_queryset(workspace),
            fields=fields if fields else None,
            many=True,
        ).data
        return Response(workspaces, status=status.HTTP_200_OK)


class WeekInMonth(Func):
    """
    This class returns the week in month
    """

    function = "FLOOR"
    template = "(((%(expressions)s - 1) / 7) + 1)::INTEGER"


class UserWorkspaceDashboardEndpoint(BaseAPIView):
    """
    This endpoint returns the user workspace dashboard details
    """

    def get(self, request, workspace_slug):
        issue_activities = (
            IssueActivity.objects.filter(
                actor=request.user,
                workspace__slug=workspace_slug,
                created_at__date__gte=date.today() + relativedelta(months=-3),
            )
            .annotate(created_date=Cast("created_at", DateField()))
            .values("created_date")
            .annotate(activity_count=Count("created_date"))
            .order_by("created_date")
        )

        month = request.GET.get("month", 1)

        completed_issues = (
            Issue.issue_objects.filter(
                assignees__in=[request.user],
                workspace__slug=workspace_slug,
                completed_at__month=month,
                completed_at__isnull=False,
            )
            .annotate(day_of_month=ExtractDay("completed_at"))
            .annotate(week_in_month=WeekInMonth(F("day_of_month")))
            .values("week_in_month")
            .annotate(completed_count=Count("id"))
            .order_by("week_in_month")
        )

        assigned_issues = Issue.issue_objects.filter(
            workspace__slug=workspace_slug, assignees__in=[request.user]
        ).count()

        pending_issues_count = Issue.issue_objects.filter(
            ~Q(state__group__in=["completed", "cancelled"]),
            workspace__slug=workspace_slug,
            assignees__in=[request.user],
        ).count()

        completed_issues_count = Issue.issue_objects.filter(
            workspace__slug=workspace_slug,
            assignees__in=[request.user],
            state__group="completed",
        ).count()

        issues_due_week = (
            Issue.issue_objects.filter(
                workspace__slug=workspace_slug,
                assignees__in=[request.user],
            )
            .annotate(target_week=ExtractWeek("target_date"))
            .filter(target_week=timezone.now().date().isocalendar()[1])
            .count()
        )

        state_distribution = (
            Issue.issue_objects.filter(
                workspace__slug=workspace_slug, assignees__in=[request.user]
            )
            .annotate(state_group=F("state__group"))
            .values("state_group")
            .annotate(state_count=Count("state_group"))
            .order_by("state_group")
        )

        overdue_issues = Issue.issue_objects.filter(
            ~Q(state__group__in=["completed", "cancelled"]),
            workspace__slug=workspace_slug,
            assignees__in=[request.user],
            target_date__lt=timezone.now(),
            completed_at__isnull=True,
        ).values("id", "name", "workspace__slug", "project_id", "target_date")

        upcoming_issues = Issue.issue_objects.filter(
            ~Q(state__group__in=["completed", "cancelled"]),
            start_date__gte=timezone.now(),
            workspace__slug=workspace_slug,
            assignees__in=[request.user],
            completed_at__isnull=True,
        ).values("id", "name", "workspace__slug", "project_id", "start_date")

        return Response(
            {
                "issue_activities": issue_activities,
                "completed_issues": completed_issues,
                "assigned_issues_count": assigned_issues,
                "pending_issues_count": pending_issues_count,
                "completed_issues_count": completed_issues_count,
                "issues_due_week_count": issues_due_week,
                "state_distribution": state_distribution,
                "overdue_issues": overdue_issues,
                "upcoming_issues": upcoming_issues,
            },
            status=status.HTTP_200_OK,
        )


class WorkspaceUserProfileStatsEndpoint(BaseAPIView):
    """
    This endpoint returns the user profile stats
    """

    def get(self, request, workspace_slug, user_id):
        filters = issue_filters(request.query_params, "GET")

        state_distribution = (
            Issue.issue_objects.filter(
                workspace__slug=workspace_slug,
                assignees__in=[user_id],
                project__project_projectmember__member=request.user,
                project__project_projectmember__is_active=True,
            )
            .filter(**filters)
            .annotate(state_group=F("state__group"))
            .values("state_group")
            .annotate(state_count=Count("state_group"))
            .order_by("state_group")
        )

        priority_order = ["urgent", "high", "medium", "low", "none"]

        priority_distribution = (
            Issue.issue_objects.filter(
                workspace__slug=workspace_slug,
                assignees__in=[user_id],
                project__project_projectmember__member=request.user,
                project__project_projectmember__is_active=True,
            )
            .filter(**filters)
            .values("priority")
            .annotate(priority_count=Count("priority"))
            .filter(priority_count__gte=1)
            .annotate(
                priority_order=Case(
                    *[
                        When(priority=p, then=Value(i))
                        for i, p in enumerate(priority_order)
                    ],
                    default=Value(len(priority_order)),
                    output_field=IntegerField(),
                )
            )
            .order_by("priority_order")
        )

        created_issues = (
            Issue.issue_objects.filter(
                workspace__slug=workspace_slug,
                project__project_projectmember__member=request.user,
                project__project_projectmember__is_active=True,
                created_by_id=user_id,
            )
            .filter(**filters)
            .count()
        )

        assigned_issues_count = (
            Issue.issue_objects.filter(
                workspace__slug=workspace_slug,
                assignees__in=[user_id],
                project__project_projectmember__member=request.user,
                project__project_projectmember__is_active=True,
            )
            .filter(**filters)
            .count()
        )

        pending_issues_count = (
            Issue.issue_objects.filter(
                ~Q(state__group__in=["completed", "cancelled"]),
                workspace__slug=workspace_slug,
                assignees__in=[user_id],
                project__project_projectmember__member=request.user,
                project__project_projectmember__is_active=True,
            )
            .filter(**filters)
            .count()
        )

        completed_issues_count = (
            Issue.issue_objects.filter(
                workspace__slug=workspace_slug,
                assignees__in=[user_id],
                state__group="completed",
                project__project_projectmember__member=request.user,
                project__project_projectmember__is_active=True,
            )
            .filter(**filters)
            .count()
        )

        subscribed_issues_count = (
            IssueSubscriber.objects.filter(
                workspace__slug=workspace_slug,
                subscriber_id=user_id,
                project__project_projectmember__member=request.user,
                project__project_projectmember__is_active=True,
                project__archived_at__isnull=True,
            )
            .filter(**filters)
            .count()
        )

        upcoming_cycles = CycleIssue.objects.filter(
            workspace__slug=workspace_slug,
            cycle__start_date__gt=timezone.now().date(),
            issue__assignees__in=[
                user_id,
            ],
        ).values("cycle__name", "cycle__id", "cycle__project_id")

        present_cycle = CycleIssue.objects.filter(
            workspace__slug=workspace_slug,
            cycle__start_date__lt=timezone.now().date(),
            cycle__end_date__gt=timezone.now().date(),
            issue__assignees__in=[
                user_id,
            ],
        ).values("cycle__name", "cycle__id", "cycle__project_id")

        return Response(
            {
                "state_distribution": state_distribution,
                "priority_distribution": priority_distribution,
                "created_issues": created_issues,
                "assigned_issues": assigned_issues_count,
                "completed_issues": completed_issues_count,
                "pending_issues": pending_issues_count,
                "subscribed_issues": subscribed_issues_count,
                "present_cycles": present_cycle,
                "upcoming_cycles": upcoming_cycles,
            }
        )


class WorkspaceUserActivityEndpoint(BaseAPIView):
    """
    This endpoint returns the user activity
    """

    permission_classes = [
        WorkspaceEntityPermission,
    ]

    def get(self, request, workspace_slug, user_id):
        projects = request.query_params.getlist("project", [])

        queryset = IssueActivity.objects.filter(
            ~Q(field__in=["comment", "vote", "reaction", "draft"]),
            workspace__slug=workspace_slug,
            project__project_projectmember__member=request.user,
            project__project_projectmember__is_active=True,
            project__archived_at__isnull=True,
            actor=user_id,
        ).select_related("actor", "workspace", "issue", "project")

        if projects:
            queryset = queryset.filter(project__in=projects)

        return self.paginate(
            request=request,
            queryset=queryset,
            on_results=lambda issue_activities: IssueActivitySerializer(
                issue_activities, many=True
            ).data,
        )


class WorkspaceUserProfileIssuesEndpoint(BaseAPIView):
    """
    This endpoint returns the user profile issues
    """

    permission_classes = [
        WorkspaceUserPermission,
    ]

    def get(self, request, workspace_slug, user_id):
        fields = [field for field in request.GET.get("fields", "").split(",") if field]
        filters = issue_filters(request.query_params, "GET")

        # Custom ordering for priority and state
        priority_order = ["urgent", "high", "medium", "low", "none"]
        state_order = [
            "backlog",
            "unstarted",
            "started",
            "completed",
            "cancelled",
        ]

        order_by_param = request.GET.get("order_by", "-created_at")
        issue_queryset = (
            Issue.issue_objects.filter(
                Q(assignees__in=[user_id])
                | Q(created_by_id=user_id)
                | Q(issue_subscribers__subscriber_id=user_id),
                workspace__slug=workspace_slug,
                project__project_projectmember__member=request.user,
                project__project_projectmember__is_active=True,
            )
            .filter(**filters)
            .select_related("workspace", "project", "state", "parent")
            .prefetch_related("assignees", "labels", "issue_module__module")
            .annotate(cycle_id=F("issue_cycle__cycle_id"))
            .annotate(
                link_count=IssueLink.objects.filter(issue=OuterRef("id"))
                .order_by()
                .annotate(count=Func(F("id"), function="Count"))
                .values("count")
            )
            .annotate(
                attachment_count=IssueAttachment.objects.filter(issue=OuterRef("id"))
                .order_by()
                .annotate(count=Func(F("id"), function="Count"))
                .values("count")
            )
            .annotate(
                sub_issues_count=Issue.issue_objects.filter(parent=OuterRef("id"))
                .order_by()
                .annotate(count=Func(F("id"), function="Count"))
                .values("count")
            )
            .annotate(
                label_ids=Coalesce(
                    ArrayAgg(
                        "labels__id",
                        distinct=True,
                        filter=~Q(labels__id__isnull=True),
                    ),
                    Value([], output_field=ArrayField(BigIntegerField())),
                ),
                assignee_ids=Coalesce(
                    ArrayAgg(
                        "assignees__id",
                        distinct=True,
                        filter=~Q(assignees__id__isnull=True)
                        & Q(assignees__member_project__is_active=True),
                    ),
                    Value([], output_field=ArrayField(BigIntegerField())),
                ),
                module_ids=Coalesce(
                    ArrayAgg(
                        "issue_module__module_id",
                        distinct=True,
                        filter=~Q(issue_module__module_id__isnull=True),
                    ),
                    Value([], output_field=ArrayField(BigIntegerField())),
                ),
            )
            .order_by("created_at")
        ).distinct()

        # Priority Ordering
        if order_by_param == "priority" or order_by_param == "-priority":
            priority_order = (
                priority_order if order_by_param == "priority" else priority_order[::-1]
            )
            issue_queryset = issue_queryset.annotate(
                priority_order=Case(
                    *[
                        When(priority=p, then=Value(i))
                        for i, p in enumerate(priority_order)
                    ],
                    output_field=CharField(),
                )
            ).order_by("priority_order")

        # State Ordering
        elif order_by_param in [
            "state__name",
            "state__group",
            "-state__name",
            "-state__group",
        ]:
            state_order = (
                state_order
                if order_by_param in ["state__name", "state__group"]
                else state_order[::-1]
            )
            issue_queryset = issue_queryset.annotate(
                state_order=Case(
                    *[
                        When(state__group=state_group, then=Value(i))
                        for i, state_group in enumerate(state_order)
                    ],
                    default=Value(len(state_order)),
                    output_field=CharField(),
                )
            ).order_by("state_order")
        # assignee and label ordering
        elif order_by_param in [
            "labels__name",
            "-labels__name",
            "assignees__first_name",
            "-assignees__first_name",
        ]:
            issue_queryset = issue_queryset.annotate(
                max_values=Max(
                    order_by_param[1::]
                    if order_by_param.startswith("-")
                    else order_by_param
                )
            ).order_by(
                "-max_values" if order_by_param.startswith("-") else "max_values"
            )
        else:
            issue_queryset = issue_queryset.order_by(order_by_param)

        issues = IssueSerializer(
            issue_queryset, many=True, fields=fields if fields else None
        ).data
        return Response(issues, status=status.HTTP_200_OK)


class WorkspaceLabelsEndpoint(BaseAPIView):
    """
    This endpoint returns the workspace labels
    """

    permission_classes = [
        WorkspaceUserPermission,
    ]

    def get(self, request, workspace_slug):
        labels = Label.objects.filter(
            workspace__slug=workspace_slug,
            project__archived_at__isnull=True,
            project__project_projectmember__member=request.user,
            project__project_projectmember__is_active=True,
        )
        serializer = LabelSerializer(labels, many=True).data
        return Response(serializer, status=status.HTTP_200_OK)


class WorkspaceStatesEndpoint(BaseAPIView):
    """
    This endpoint returns the workspace states
    """

    permission_classes = [
        WorkspaceEntityPermission,
    ]

    def get(self, request, workspace_slug):
        states = State.objects.filter(
            workspace__slug=workspace_slug,
            project__project_projectmember__member=request.user,
            project__project_projectmember__is_active=True,
            project__archived_at__isnull=True,
        )
        serializer = StateSerializer(states, many=True).data
        return Response(serializer, status=status.HTTP_200_OK)


class WorkspaceEstimatesEndpoint(BaseAPIView):
    """
    This endpoint returns the workspace estimates
    """

    permission_classes = [
        WorkspaceEntityPermission,
    ]

    def get(self, request, workspace_slug):
        estimate_ids = Project.objects.filter(
            workspace__slug=workspace_slug, estimate__isnull=False
        ).values_list("estimate_id", flat=True)
        estimates = Estimate.objects.filter(pk__in=estimate_ids).prefetch_related(
            Prefetch(
                "points",
                queryset=EstimatePoint.objects.select_related(
                    "estimate", "workspace", "project"
                ),
            )
        )
        serializer = EstimatePointReadSerializer(estimates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WorkspaceModulesEndpoint(BaseAPIView):
    """
    This endpoint returns the workspace modules
    """

    permission_classes = [
        WorkspaceUserPermission,
    ]

    def get(self, request, workspace_slug):
        modules = (
            Module.objects.filter(workspace__slug=workspace_slug)
            .select_related("project")
            .select_related("workspace")
            .select_related("lead")
            .prefetch_related("members")
            .filter(archived_at__isnull=False)
            .prefetch_related(
                Prefetch(
                    "link_module",
                    queryset=ModuleLink.objects.select_related("module", "created_by"),
                )
            )
            .annotate(
                total_issues=Count(
                    "issue_module",
                    filter=Q(
                        issue_module__issue__archived_at__isnull=True,
                        issue_module__issue__is_draft=False,
                    ),
                    distinct=True,
                ),
            )
            .annotate(
                completed_issues=Count(
                    "issue_module__issue__state__group",
                    filter=Q(
                        issue_module__issue__state__group="completed",
                        issue_module__issue__archived_at__isnull=True,
                        issue_module__issue__is_draft=False,
                    ),
                    distinct=True,
                )
            )
            .annotate(
                cancelled_issues=Count(
                    "issue_module__issue__state__group",
                    filter=Q(
                        issue_module__issue__state__group="cancelled",
                        issue_module__issue__archived_at__isnull=True,
                        issue_module__issue__is_draft=False,
                    ),
                    distinct=True,
                )
            )
            .annotate(
                started_issues=Count(
                    "issue_module__issue__state__group",
                    filter=Q(
                        issue_module__issue__state__group="started",
                        issue_module__issue__archived_at__isnull=True,
                        issue_module__issue__is_draft=False,
                    ),
                    distinct=True,
                )
            )
            .annotate(
                unstarted_issues=Count(
                    "issue_module__issue__state__group",
                    filter=Q(
                        issue_module__issue__state__group="unstarted",
                        issue_module__issue__archived_at__isnull=True,
                        issue_module__issue__is_draft=False,
                    ),
                    distinct=True,
                )
            )
            .annotate(
                backlog_issues=Count(
                    "issue_module__issue__state__group",
                    filter=Q(
                        issue_module__issue__state__group="backlog",
                        issue_module__issue__archived_at__isnull=True,
                        issue_module__issue__is_draft=False,
                    ),
                    distinct=True,
                )
            )
            .order_by(self.kwargs.get("order_by", "-created_at"))
        )

        serializer = ModuleSerializer(modules, many=True).data
        return Response(serializer, status=status.HTTP_200_OK)


class WorkspaceCyclesEndpoint(BaseAPIView):
    """
    This endpoint returns the workspace cycles
    """

    permission_classes = [
        WorkspaceUserPermission,
    ]

    def get(self, request, workspace_slug):
        cycles = (
            Cycle.objects.filter(workspace__slug=workspace_slug)
            .select_related("project")
            .select_related("workspace")
            .select_related("owned_by")
            .filter(archived_at__isnull=False)
            .annotate(
                total_issues=Count(
                    "issue_cycle",
                    filter=Q(
                        issue_cycle__issue__archived_at__isnull=True,
                        issue_cycle__issue__is_draft=False,
                    ),
                )
            )
            .annotate(
                completed_issues=Count(
                    "issue_cycle__issue__state__group",
                    filter=Q(
                        issue_cycle__issue__state__group="completed",
                        issue_cycle__issue__archived_at__isnull=True,
                        issue_cycle__issue__is_draft=False,
                    ),
                )
            )
            .annotate(
                cancelled_issues=Count(
                    "issue_cycle__issue__state__group",
                    filter=Q(
                        issue_cycle__issue__state__group="cancelled",
                        issue_cycle__issue__archived_at__isnull=True,
                        issue_cycle__issue__is_draft=False,
                    ),
                )
            )
            .annotate(
                started_issues=Count(
                    "issue_cycle__issue__state__group",
                    filter=Q(
                        issue_cycle__issue__state__group="started",
                        issue_cycle__issue__archived_at__isnull=True,
                        issue_cycle__issue__is_draft=False,
                    ),
                )
            )
            .annotate(
                unstarted_issues=Count(
                    "issue_cycle__issue__state__group",
                    filter=Q(
                        issue_cycle__issue__state__group="unstarted",
                        issue_cycle__issue__archived_at__isnull=True,
                        issue_cycle__issue__is_draft=False,
                    ),
                )
            )
            .annotate(
                backlog_issues=Count(
                    "issue_cycle__issue__state__group",
                    filter=Q(
                        issue_cycle__issue__state__group="backlog",
                        issue_cycle__issue__archived_at__isnull=True,
                        issue_cycle__issue__is_draft=False,
                    ),
                )
            )
            .annotate(total_estimates=Sum("issue_cycle__issue__estimate_point"))
            .annotate(
                completed_estimates=Sum(
                    "issue_cycle__issue__estimate_point",
                    filter=Q(
                        issue_cycle__issue__state__group="completed",
                        issue_cycle__issue__archived_at__isnull=True,
                        issue_cycle__issue__is_draft=False,
                    ),
                )
            )
            .annotate(
                started_estimates=Sum(
                    "issue_cycle__issue__estimate_point",
                    filter=Q(
                        issue_cycle__issue__state__group="started",
                        issue_cycle__issue__archived_at__isnull=True,
                        issue_cycle__issue__is_draft=False,
                    ),
                )
            )
            .order_by(self.kwargs.get("order_by", "-created_at"))
            .distinct()
        )
        serializer = CycleSerializer(cycles, many=True).data
        return Response(serializer, status=status.HTTP_200_OK)


class UserActivityEndpoint(BaseAPIView, BasePaginator):
    def get(self, request):
        queryset = IssueActivity.objects.filter(actor=request.user).select_related(
            "actor", "workspace", "issue", "project"
        )

        return self.paginate(
            request=request,
            queryset=queryset,
            on_results=lambda issue_activities: IssueActivitySerializer(
                issue_activities, many=True
            ).data,
        )


class UserProfileProjectsStatisticsEndpoint(BaseAPIView):
    """
    This endpoint returns the user profile along with the user's project stats
    """

    def get(self, request, workspace_slug, user_id):
        user_data = User.objects.get(pk=user_id)
        requesting_workspace_member = WorkspaceMember.objects.get(
            workspace__slug=workspace_slug,
            member=request.user,
            is_active=True,
        )
        projects = []
        if requesting_workspace_member.role >= ERole.MEMBER.value:
            projects = (
                Project.objects.filter(
                    workspace__slug=workspace_slug,
                    project_projectmember__member=request.user,
                    project_projectmember__is_active=True,
                    archived_at__isnull=True,
                )
                .annotate(
                    created_issues=Count(
                        "project_issue",
                        filter=Q(
                            project_issue__created_by_id=user_id,
                            project_issue__archived_at__isnull=True,
                            project_issue__is_draft=False,
                        ),
                    )
                )
                .annotate(
                    assigned_issues=Count(
                        "project_issue",
                        filter=Q(
                            project_issue__assignees__in=[user_id],
                            project_issue__archived_at__isnull=True,
                            project_issue__is_draft=False,
                        ),
                    )
                )
                .annotate(
                    completed_issues=Count(
                        "project_issue",
                        filter=Q(
                            project_issue__completed_at__isnull=False,
                            project_issue__assignees__in=[user_id],
                            project_issue__archived_at__isnull=True,
                            project_issue__is_draft=False,
                        ),
                    )
                )
                .annotate(
                    pending_issues=Count(
                        "project_issue",
                        filter=Q(
                            project_issue__state__group__in=[
                                "backlog",
                                "unstarted",
                                "started",
                            ],
                            project_issue__assignees__in=[user_id],
                            project_issue__archived_at__isnull=True,
                            project_issue__is_draft=False,
                        ),
                    )
                )
                .values(
                    "id",
                    "name",
                    "identifier",
                    "emoji",
                    "icon_prop",
                    "created_issues",
                    "assigned_issues",
                    "completed_issues",
                    "pending_issues",
                )
            )
        return Response(
            {
                "project_data": projects,
                "user_data": {
                    "email": user_data.email,
                    "first_name": user_data.first_name,
                    "last_name": user_data.last_name,
                    "avatar": user_data.avatar,
                    "cover_image": user_data.cover_image,
                    "date_joined": user_data.created_at,
                    "user_timezone": user_data.user_timezone,
                    "display_name": user_data.display_name,
                },
            },
            status=status.HTTP_200_OK,
        )
