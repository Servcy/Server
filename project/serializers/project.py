from rest_framework import serializers

from app.serializers import ServcyBaseSerializer, ServcyDynamicBaseSerializer
from iam.serializers import (
    UserAdminLiteSerializer,
    UserLiteSerializer,
    WorkspaceLiteSerializer,
)
from project.models import (
    Project,
    ProjectDeployBoard,
    ProjectFavorite,
    ProjectIdentifier,
    ProjectMember,
    ProjectPublicMember,
    ProjectTemplate,
)


class ProjectTemplateSerializer(ServcyBaseSerializer):
    workspace_detail = WorkspaceLiteSerializer(source="workspace", read_only=True)

    class Meta:
        model = ProjectTemplate
        fields = "__all__"
        read_only_fields = [
            "workspace",
        ]


class ProjectSerializer(ServcyBaseSerializer):
    workspace_detail = WorkspaceLiteSerializer(source="workspace", read_only=True)

    class Meta:
        model = Project
        fields = "__all__"
        read_only_fields = [
            "workspace",
        ]

    def create(self, validated_data):
        identifier = validated_data.get("identifier", "").strip().upper()
        if identifier == "":
            raise serializers.ValidationError(detail="Project Identifier is required")

        if ProjectIdentifier.objects.filter(
            name=identifier, workspace_id=self.context["workspace_id"]
        ).exists():
            raise serializers.ValidationError(detail="Project Identifier is taken")
        project = Project.objects.create(
            **validated_data, workspace_id=self.context["workspace_id"]
        )
        _ = ProjectIdentifier.objects.create(
            name=project.identifier,
            project=project,
            workspace_id=self.context["workspace_id"],
        )
        return project

    def update(self, instance, validated_data):
        identifier = validated_data.get("identifier", "").strip().upper()

        # If identifier is not passed update the project and return
        if identifier == "":
            project = super().update(instance, validated_data)
            return project

        # If no Project Identifier is found create it
        project_identifier = ProjectIdentifier.objects.filter(
            name=identifier, workspace_id=instance.workspace_id
        ).first()
        if project_identifier is None:
            project = super().update(instance, validated_data)
            project_identifier = ProjectIdentifier.objects.filter(
                project=project
            ).first()
            if project_identifier is not None:
                project_identifier.name = identifier
                project_identifier.save()
            return project
        # If found check if the project_id to be updated and identifier project id is same
        if project_identifier.project_id == instance.id:
            # If same pass update
            project = super().update(instance, validated_data)
            return project

        # If not same fail update
        raise serializers.ValidationError(detail="Project Identifier is already taken")


class ProjectLiteSerializer(ServcyBaseSerializer):
    class Meta:
        model = Project
        fields = [
            "id",
            "identifier",
            "name",
            "cover_image",
            "icon_prop",
            "emoji",
            "description",
        ]
        read_only_fields = fields


class ProjectUltraLiteSerializer(ServcyBaseSerializer):
    class Meta:
        model = Project
        fields = [
            "id",
            "identifier",
        ]
        read_only_fields = fields


class ProjectListSerializer(ServcyDynamicBaseSerializer):
    total_issues = serializers.IntegerField(read_only=True)
    archived_issues = serializers.IntegerField(read_only=True)
    archived_sub_issues = serializers.IntegerField(read_only=True)
    draft_issues = serializers.IntegerField(read_only=True)
    draft_sub_issues = serializers.IntegerField(read_only=True)
    sub_issues = serializers.IntegerField(read_only=True)
    is_favorite = serializers.BooleanField(read_only=True)
    total_members = serializers.IntegerField(read_only=True)
    total_cycles = serializers.IntegerField(read_only=True)
    total_modules = serializers.IntegerField(read_only=True)
    is_member = serializers.BooleanField(read_only=True)
    sort_order = serializers.FloatField(read_only=True)
    member_role = serializers.IntegerField(read_only=True)
    is_deployed = serializers.BooleanField(read_only=True)
    members = serializers.SerializerMethodField()
    budget = serializers.SerializerMethodField()

    def get_budget(self, obj):
        project_budget = getattr(obj, "budget", None)
        if project_budget is not None:
            return {
                "id": project_budget.id,
                "amount": project_budget.amount,
                "currency": project_budget.currency,
            }
        return {
            "id": None,
            "amount": "",
            "currency": "USD",
        }

    def get_members(self, obj):
        project_members = getattr(obj, "members_list", None)
        if project_members is not None:
            # Filter members by the project ID
            return [
                {
                    "id": member.id,
                    "member_id": member.member_id,
                    "member__display_name": member.member.display_name,
                    "member__avatar": member.member.avatar,
                }
                for member in project_members
            ]
        return []

    class Meta:
        model = Project
        fields = "__all__"


class ProjectDetailSerializer(ServcyBaseSerializer):
    default_assignee = UserLiteSerializer(read_only=True)
    lead = UserLiteSerializer(read_only=True)
    is_favorite = serializers.BooleanField(read_only=True)
    total_members = serializers.IntegerField(read_only=True)
    total_cycles = serializers.IntegerField(read_only=True)
    total_modules = serializers.IntegerField(read_only=True)
    is_member = serializers.BooleanField(read_only=True)
    sort_order = serializers.FloatField(read_only=True)
    member_role = serializers.IntegerField(read_only=True)
    is_deployed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Project
        fields = "__all__"


class ProjectMemberSerializer(ServcyBaseSerializer):
    workspace = WorkspaceLiteSerializer(read_only=True)
    project = ProjectLiteSerializer(read_only=True)
    member = UserLiteSerializer(read_only=True)
    rate = serializers.SerializerMethodField()

    def get_rate(self, obj):
        member_cost = getattr(obj, "rate", None)
        if member_cost is not None:
            return {
                "id": member_cost.id,
                "rate": member_cost.rate if member_cost.rate else "",
                "currency": member_cost.currency,
                "per_hour_or_per_project": member_cost.per_hour_or_per_project,
            }
        return {
            "id": None,
            "rate": "",
            "currency": "USD",
            "per_hour_or_per_project": True,
        }

    class Meta:
        model = ProjectMember
        fields = "__all__"


class ProjectMemberAdminSerializer(ServcyBaseSerializer):
    workspace = WorkspaceLiteSerializer(read_only=True)
    project = ProjectLiteSerializer(read_only=True)
    member = UserAdminLiteSerializer(read_only=True)

    class Meta:
        model = ProjectMember
        fields = "__all__"


class ProjectMemberRoleSerializer(ServcyDynamicBaseSerializer):
    rate = serializers.SerializerMethodField()

    def get_rate(self, obj):
        member_cost = getattr(obj, "rate", None)
        if member_cost is not None:
            return {
                "id": member_cost.id,
                "rate": member_cost.rate if member_cost.rate else "",
                "currency": member_cost.currency,
                "per_hour_or_per_project": member_cost.per_hour_or_per_project,
            }
        return {
            "id": None,
            "rate": "",
            "currency": "USD",
            "per_hour_or_per_project": True,
        }

    class Meta:
        model = ProjectMember
        fields = ("id", "role", "member", "project", "rate")


class ProjectIdentifierSerializer(ServcyBaseSerializer):
    class Meta:
        model = ProjectIdentifier
        fields = "__all__"


class ProjectFavoriteSerializer(ServcyBaseSerializer):
    class Meta:
        model = ProjectFavorite
        fields = "__all__"
        read_only_fields = [
            "workspace",
            "user",
        ]


class ProjectDeployBoardSerializer(ServcyBaseSerializer):
    project_details = ProjectLiteSerializer(read_only=True, source="project")
    workspace_detail = WorkspaceLiteSerializer(read_only=True, source="workspace")

    class Meta:
        model = ProjectDeployBoard
        fields = "__all__"
        read_only_fields = [
            "workspace",
            "project",
            "anchor",
        ]


class ProjectPublicMemberSerializer(ServcyBaseSerializer):
    class Meta:
        model = ProjectPublicMember
        fields = "__all__"
        read_only_fields = [
            "workspace",
            "project",
            "member",
        ]
