from rest_framework.exceptions import ValidationError

from iam.enums import ERole
from project.models import IssueProperty, Project, ProjectMember, ProjectMemberRate
from project.serializers import ProjectMemberRoleSerializer


def add_project_member_if_not_exists(
    members, workspace_slug, project_id, user, return_serialized_data=True
):
    if not len(members):
        raise ValidationError()
    # Get the project
    project = Project.objects.get(pk=project_id, workspace__slug=workspace_slug)
    bulk_project_members = []
    existing_project_members = []
    bulk_issue_props = []
    bulk_project_member_costs = []
    # Create a dictionary of member_id and their roles
    member_roles = {}
    # Create a dictionary of member_id and their costs
    member_costs = {}
    member_ids = []
    for member in members:
        member_id = member.get("member_id")
        member_ids.append(member_id)
        member_roles[member_id] = member.get("role", ERole.MEMBER.value)
        try:
            cost = float(member.get("rate", 0))
        except ValueError:
            cost = 0
        member_costs[member_id] = {
            "rate": cost,
            "currency": member.get("currency", "USD"),
            "per_hour_or_per_project": member.get("per_hour_or_per_project", True),
        }
    for project_member in ProjectMember.objects.filter(
        project_id=project_id,
        member_id__in=member_ids,
    ):
        project_member.role = member_roles.get(project_member.member_id)
        project_member.is_active = True
        project_member_id = project_member.member_id
        if not project_member.rate:
            project_member_cost = ProjectMemberRate.objects.create(
                project_member=project_member,
                rate=member_costs[project_member_id].get("rate", 0),
                currency=member_costs[project_member_id].get("currency", "USD"),
                per_hour_or_per_project=member_costs[project_member_id].get(
                    "per_hour_or_per_project", True
                ),
                project=project,
                workspace=project.workspace,
                created_by=user,
                updated_by=user,
            )
            project_member.rate = project_member_cost
        else:
            project_member_rate = project_member.rate
            project_member_rate.rate = member_costs[project_member_id].get("rate", 0)
            project_member_rate.currency = member_costs[project_member_id].get(
                "currency", "USD"
            )
            project_member_rate.per_hour_or_per_project = member_costs[
                project_member_id
            ].get("per_hour_or_per_project", True)
            bulk_project_member_costs.append(project_member_rate)
            member_costs.pop(project_member_id, None)
        # this is to update the role, is_active and rate of the existing members
        bulk_project_members.append(project_member)
        # this is to track the existing members
        existing_project_members.append(project_member_id)
    # Update the roles of the existing members
    ProjectMember.objects.bulk_update(
        bulk_project_members, ["is_active", "role", "rate"], batch_size=100
    )
    # Update the rates of the existing members
    ProjectMemberRate.objects.bulk_update(
        bulk_project_member_costs,
        ["rate", "currency", "per_hour_or_per_project"],
        batch_size=10,
    )
    # Get the updated existing project members for constructing sorted order
    project_members = (
        ProjectMember.objects.filter(
            workspace__slug=workspace_slug,
            project_id=project_id,
            member_id__in=member_ids,
        )
        .values("member_id", "sort_order")
        .order_by("sort_order")
    )
    bulk_project_members = []
    for member in members:
        member_id = member.get("member_id")
        member_role = member.get("role", ERole.MEMBER.value)
        bulk_issue_props.append(
            IssueProperty(
                user_id=member_id,
                project_id=project_id,
                workspace_id=project.workspace_id,
                created_by=user,
                updated_by=user,
            )
        )
        if member_id in existing_project_members:
            continue
        sort_order = [
            project_member.get("sort_order")
            for project_member in project_members
            if project_member.get("member_id") == member_id
        ]
        project_member = ProjectMember.objects.create(
            member_id=member_id,
            role=member_role,
            project_id=project_id,
            workspace_id=project.workspace_id,
            sort_order=sort_order[0] - 10000 if len(sort_order) else 65535,
        )
        project_member_cost = ProjectMemberRate.objects.create(
            project_member=project_member,
            rate=member_costs[project_member.member_id].get("rate", 0),
            currency=member_costs[project_member.member_id].get("currency", "USD"),
            per_hour_or_per_project=member_costs[project_member.member_id].get(
                "per_hour_or_per_project", True
            ),
            project=project,
            workspace=project.workspace,
            created_by=user,
            updated_by=user,
        )
        project_member.rate = project_member_cost
        bulk_project_members.append(project_member)
    ProjectMember.objects.bulk_update(bulk_project_members, ["rate"], batch_size=100)
    IssueProperty.objects.bulk_create(
        bulk_issue_props, batch_size=10, ignore_conflicts=True
    )
    if return_serialized_data:
        project_members = ProjectMember.objects.filter(
            project_id=project_id,
            member_id__in=member_ids,
        )
        serializer = ProjectMemberRoleSerializer(project_members, many=True)
        return serializer.data
