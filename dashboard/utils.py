from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.postgres.fields import ArrayField
from django.db.models import (
    BigIntegerField,
    Case,
    CharField,
    Count,
    F,
    Func,
    OuterRef,
    Prefetch,
    Q,
    Value,
    When,
)
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from project.models import (
    Issue,
    IssueActivity,
    IssueAttachment,
    IssueLink,
    IssueRelation,
    Project,
    ProjectMember,
)
from project.serializers import IssueActivitySerializer, IssueSerializer
from project.utils.filters import issue_filters


def dashboard_overview_stats(self, request, workspace_slug):
    assigned_issues = Issue.issue_objects.filter(
        project__project_projectmember__is_active=True,
        project__project_projectmember__member=request.user,
        workspace__slug=workspace_slug,
        assignees__in=[request.user],
    ).count()

    pending_issues_count = Issue.issue_objects.filter(
        ~Q(state__group__in=["completed", "cancelled"]),
        target_date__lt=timezone.now().date(),
        project__project_projectmember__is_active=True,
        project__project_projectmember__member=request.user,
        workspace__slug=workspace_slug,
        assignees__in=[request.user],
    ).count()

    created_issues_count = Issue.issue_objects.filter(
        workspace__slug=workspace_slug,
        project__project_projectmember__is_active=True,
        project__project_projectmember__member=request.user,
        created_by_id=request.user.id,
    ).count()

    completed_issues_count = Issue.issue_objects.filter(
        workspace__slug=workspace_slug,
        project__project_projectmember__is_active=True,
        project__project_projectmember__member=request.user,
        assignees__in=[request.user],
        state__group="completed",
    ).count()

    return Response(
        {
            "assigned_issues_count": assigned_issues,
            "pending_issues_count": pending_issues_count,
            "completed_issues_count": completed_issues_count,
            "created_issues_count": created_issues_count,
        },
        status=status.HTTP_200_OK,
    )


def dashboard_assigned_issues(self, request, workspace_slug):
    filters = issue_filters(request.query_params, "GET")
    issue_type = request.GET.get("issue_type", None)

    # get all the assigned issues
    assigned_issues = (
        Issue.issue_objects.filter(
            workspace__slug=workspace_slug,
            project__project_projectmember__member=request.user,
            project__project_projectmember__is_active=True,
            assignees__in=[request.user],
        )
        .filter(**filters)
        .select_related("workspace", "project", "state", "parent")
        .prefetch_related("assignees", "labels", "issue_module__module")
        .prefetch_related(
            Prefetch(
                "issue_relation",
                queryset=IssueRelation.objects.select_related(
                    "related_issue"
                ).select_related("issue"),
            )
        )
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
    )

    # Priority Ordering
    priority_order = ["urgent", "high", "medium", "low", "none"]
    assigned_issues = assigned_issues.annotate(
        priority_order=Case(
            *[When(priority=p, then=Value(i)) for i, p in enumerate(priority_order)],
            output_field=CharField(),
        )
    ).order_by("priority_order")

    if issue_type == "pending":
        pending_issues_count = assigned_issues.filter(
            state__group__in=["backlog", "started", "unstarted"]
        ).count()
        pending_issues = assigned_issues.filter(
            state__group__in=["backlog", "started", "unstarted"]
        )[:5]
        return Response(
            {
                "issues": IssueSerializer(
                    pending_issues, many=True, expand=self.expand
                ).data,
                "count": pending_issues_count,
            },
            status=status.HTTP_200_OK,
        )

    if issue_type == "completed":
        completed_issues_count = assigned_issues.filter(
            state__group__in=["completed"]
        ).count()
        completed_issues = assigned_issues.filter(state__group__in=["completed"])[:5]
        return Response(
            {
                "issues": IssueSerializer(
                    completed_issues, many=True, expand=self.expand
                ).data,
                "count": completed_issues_count,
            },
            status=status.HTTP_200_OK,
        )

    if issue_type == "overdue":
        overdue_issues_count = assigned_issues.filter(
            state__group__in=["backlog", "unstarted", "started"],
            target_date__lt=timezone.now(),
        ).count()
        overdue_issues = assigned_issues.filter(
            state__group__in=["backlog", "unstarted", "started"],
            target_date__lt=timezone.now(),
        )[:5]
        return Response(
            {
                "issues": IssueSerializer(
                    overdue_issues, many=True, expand=self.expand
                ).data,
                "count": overdue_issues_count,
            },
            status=status.HTTP_200_OK,
        )

    if issue_type == "upcoming":
        upcoming_issues_count = assigned_issues.filter(
            state__group__in=["backlog", "unstarted", "started"],
            target_date__gte=timezone.now(),
        ).count()
        upcoming_issues = assigned_issues.filter(
            state__group__in=["backlog", "unstarted", "started"],
            target_date__gte=timezone.now(),
        )[:5]
        return Response(
            {
                "issues": IssueSerializer(
                    upcoming_issues, many=True, expand=self.expand
                ).data,
                "count": upcoming_issues_count,
            },
            status=status.HTTP_200_OK,
        )

    return Response(
        {"error": "Please specify a valid issue type"},
        status=status.HTTP_400_BAD_REQUEST,
    )


def dashboard_created_issues(self, request, workspace_slug):
    filters = issue_filters(request.query_params, "GET")
    issue_type = request.GET.get("issue_type", None)

    # get all the assigned issues
    created_issues = (
        Issue.issue_objects.filter(
            workspace__slug=workspace_slug,
            project__project_projectmember__member=request.user,
            project__project_projectmember__is_active=True,
            created_by=request.user,
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
    )

    # Priority Ordering
    priority_order = ["urgent", "high", "medium", "low", "none"]
    created_issues = created_issues.annotate(
        priority_order=Case(
            *[When(priority=p, then=Value(i)) for i, p in enumerate(priority_order)],
            output_field=CharField(),
        )
    ).order_by("priority_order")

    if issue_type == "pending":
        pending_issues_count = created_issues.filter(
            state__group__in=["backlog", "started", "unstarted"]
        ).count()
        pending_issues = created_issues.filter(
            state__group__in=["backlog", "started", "unstarted"]
        )[:5]
        return Response(
            {
                "issues": IssueSerializer(
                    pending_issues, many=True, expand=self.expand
                ).data,
                "count": pending_issues_count,
            },
            status=status.HTTP_200_OK,
        )

    if issue_type == "completed":
        completed_issues_count = created_issues.filter(
            state__group__in=["completed"]
        ).count()
        completed_issues = created_issues.filter(state__group__in=["completed"])[:5]
        return Response(
            {
                "issues": IssueSerializer(completed_issues, many=True).data,
                "count": completed_issues_count,
            },
            status=status.HTTP_200_OK,
        )

    if issue_type == "overdue":
        overdue_issues_count = created_issues.filter(
            state__group__in=["backlog", "unstarted", "started"],
            target_date__lt=timezone.now(),
        ).count()
        overdue_issues = created_issues.filter(
            state__group__in=["backlog", "unstarted", "started"],
            target_date__lt=timezone.now(),
        )[:5]
        return Response(
            {
                "issues": IssueSerializer(overdue_issues, many=True).data,
                "count": overdue_issues_count,
            },
            status=status.HTTP_200_OK,
        )

    if issue_type == "upcoming":
        upcoming_issues_count = created_issues.filter(
            state__group__in=["backlog", "unstarted", "started"],
            target_date__gte=timezone.now(),
        ).count()
        upcoming_issues = created_issues.filter(
            state__group__in=["backlog", "unstarted", "started"],
            target_date__gte=timezone.now(),
        )[:5]
        return Response(
            {
                "issues": IssueSerializer(upcoming_issues, many=True).data,
                "count": upcoming_issues_count,
            },
            status=status.HTTP_200_OK,
        )

    return Response(
        {"error": "Please specify a valid issue type"},
        status=status.HTTP_400_BAD_REQUEST,
    )


def dashboard_issues_by_state_groups(self, request, workspace_slug):
    filters = issue_filters(request.query_params, "GET")
    state_order = ["backlog", "unstarted", "started", "completed", "cancelled"]
    issues_by_state_groups = (
        Issue.issue_objects.filter(
            workspace__slug=workspace_slug,
            project__project_projectmember__is_active=True,
            project__project_projectmember__member=request.user,
            assignees__in=[request.user],
        )
        .filter(**filters)
        .values("state__group")
        .annotate(count=Count("id"))
    )

    # default state
    all_groups = {state: 0 for state in state_order}

    # Update counts for existing groups
    for entry in issues_by_state_groups:
        all_groups[entry["state__group"]] = entry["count"]

    # Prepare output including all groups with their counts
    output_data = [
        {"state": group, "count": count} for group, count in all_groups.items()
    ]

    return Response(output_data, status=status.HTTP_200_OK)


def dashboard_issues_by_priority(self, request, workspace_slug):
    filters = issue_filters(request.query_params, "GET")
    priority_order = ["urgent", "high", "medium", "low", "none"]

    issues_by_priority = (
        Issue.issue_objects.filter(
            workspace__slug=workspace_slug,
            project__project_projectmember__is_active=True,
            project__project_projectmember__member=request.user,
            assignees__in=[request.user],
        )
        .filter(**filters)
        .values("priority")
        .annotate(count=Count("id"))
    )

    # default priority
    all_groups = {priority: 0 for priority in priority_order}

    # Update counts for existing groups
    for entry in issues_by_priority:
        all_groups[entry["priority"]] = entry["count"]

    # Prepare output including all groups with their counts
    output_data = [
        {"priority": group, "count": count} for group, count in all_groups.items()
    ]

    return Response(output_data, status=status.HTTP_200_OK)


def dashboard_recent_activity(self, request, workspace_slug):
    queryset = IssueActivity.objects.filter(
        ~Q(field__in=["comment", "vote", "reaction", "draft"]),
        workspace__slug=workspace_slug,
        project__archived_at__isnull=True,
        project__project_projectmember__member=request.user,
        project__project_projectmember__is_active=True,
        actor=request.user,
    ).select_related("actor", "workspace", "issue", "project")[:8]

    return Response(
        IssueActivitySerializer(queryset, many=True).data,
        status=status.HTTP_200_OK,
    )


def dashboard_recent_projects(self, request, workspace_slug):
    project_ids = (
        IssueActivity.objects.filter(
            workspace__slug=workspace_slug,
            project__project_projectmember__member=request.user,
            project__project_projectmember__is_active=True,
            project__archived_at__isnull=True,
            actor=request.user,
        )
        .values_list("project_id", flat=True)
        .distinct()
    )

    # Extract project IDs from the recent projects
    unique_project_ids = set(project_id for project_id in project_ids)

    return Response(
        list(unique_project_ids)[:4],
        status=status.HTTP_200_OK,
    )


def dashboard_recent_collaborators(self, request, workspace_slug):
    # Fetch all project IDs where the user belongs to
    user_projects = Project.objects.filter(
        project_projectmember__member=request.user,
        project_projectmember__is_active=True,
        archived_at__isnull=True,
        workspace__slug=workspace_slug,
    ).values_list("id", flat=True)

    # Fetch all users who have performed an activity in the projects where the user exists
    users_with_activities = (
        IssueActivity.objects.filter(
            workspace__slug=workspace_slug,
            project_id__in=user_projects,
            project__archived_at__isnull=True,
        )
        .values("actor")
        .exclude(actor=request.user)
        .annotate(num_activities=Count("actor"))
        .order_by("-num_activities")
    )[:7]

    # Get the count of active issues for each user in users_with_activities
    users_with_active_issues = []
    for user_activity in users_with_activities:
        user_id = user_activity["actor"]
        active_issue_count = Issue.objects.filter(
            assignees__in=[user_id],
            state__group__in=["unstarted", "started"],
        ).count()
        users_with_active_issues.append(
            {"user_id": user_id, "active_issue_count": active_issue_count}
        )

    # Insert the logged-in user's ID and their active issue count at the beginning
    active_issue_count = Issue.objects.filter(
        assignees__in=[request.user],
        state__group__in=["unstarted", "started"],
    ).count()

    if users_with_activities.count() < 7:
        # Calculate the additional collaborators needed
        additional_collaborators_needed = 7 - users_with_activities.count()

        # Fetch additional collaborators from the project_member table
        additional_collaborators = list(
            set(
                ProjectMember.objects.filter(
                    ~Q(member=request.user),
                    project_id__in=user_projects,
                    workspace__slug=workspace_slug,
                    project__archived_at__isnull=True,
                )
                .exclude(member__in=[user["actor"] for user in users_with_activities])
                .values_list("member", flat=True)
            )
        )

        additional_collaborators = additional_collaborators[
            :additional_collaborators_needed
        ]

        # Append additional collaborators to the list
        for collaborator_id in additional_collaborators:
            active_issue_count = Issue.objects.filter(
                assignees__in=[collaborator_id],
                state__group__in=["unstarted", "started"],
            ).count()
            users_with_active_issues.append(
                {
                    "user_id": str(collaborator_id),
                    "active_issue_count": active_issue_count,
                }
            )

    users_with_active_issues.insert(
        0,
        {"user_id": request.user.id, "active_issue_count": active_issue_count},
    )

    return Response(users_with_active_issues, status=status.HTTP_200_OK)
