from rest_framework import serializers

from app.serializers import ServcyBaseSerializer, ServcyDynamicBaseSerializer
from iam.models import User
from project.models import (
    Module,
    ModuleFavorite,
    ModuleIssue,
    ModuleLink,
    ModuleMember,
    ModuleUserProperties,
)

from .project import ProjectLiteSerializer


class ModuleWriteSerializer(ServcyBaseSerializer):
    lead_id = serializers.PrimaryKeyRelatedField(
        source="lead",
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
    )
    member_ids = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=User.objects.all()),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Module
        fields = "__all__"
        read_only_fields = [
            "workspace",
            "project",
            "created_by",
            "updated_by",
            "archived_at",
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["member_ids"] = [str(member.id) for member in instance.members.all()]
        return data

    def validate(self, data):
        if (
            data.get("start_date", None) is not None
            and data.get("target_date", None) is not None
            and data.get("start_date", None) > data.get("target_date", None)
        ):
            raise serializers.ValidationError("Start date cannot exceed target date")
        return data

    def create(self, validated_data):
        members = validated_data.pop("member_ids", None)
        project = self.context["project"]

        module = Module.objects.create(**validated_data, project=project)
        if members is not None:
            ModuleMember.objects.bulk_create(
                [
                    ModuleMember(
                        module=module,
                        member=member,
                        project=project,
                        workspace=project.workspace,
                        created_by=module.created_by,
                        updated_by=module.updated_by,
                    )
                    for member in members
                ],
                batch_size=10,
                ignore_conflicts=True,
            )

        return module

    def update(self, instance, validated_data):
        members = validated_data.pop("member_ids", None)

        if members is not None:
            ModuleMember.objects.filter(module=instance).delete()
            ModuleMember.objects.bulk_create(
                [
                    ModuleMember(
                        module=instance,
                        member=member,
                        project=instance.project,
                        workspace=instance.project.workspace,
                        created_by=instance.created_by,
                        updated_by=instance.updated_by,
                    )
                    for member in members
                ],
                batch_size=10,
                ignore_conflicts=True,
            )

        return super().update(instance, validated_data)


class ModuleFlatSerializer(ServcyBaseSerializer):
    class Meta:
        model = Module
        fields = "__all__"
        read_only_fields = [
            "workspace",
            "project",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        ]


class ModuleIssueSerializer(ServcyBaseSerializer):
    module_detail = ModuleFlatSerializer(read_only=True, source="module")
    issue_detail = ProjectLiteSerializer(read_only=True, source="issue")
    sub_issues_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ModuleIssue
        fields = "__all__"
        read_only_fields = [
            "workspace",
            "project",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            "module",
        ]


class ModuleLinkSerializer(ServcyBaseSerializer):
    class Meta:
        model = ModuleLink
        fields = "__all__"
        read_only_fields = [
            "workspace",
            "project",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            "module",
        ]

    # Validation if url already exists
    def create(self, validated_data):
        if ModuleLink.objects.filter(
            url=validated_data.get("url"),
            module_id=validated_data.get("module_id"),
        ).exists():
            raise serializers.ValidationError(
                {"error": "URL already exists for this Issue"}
            )
        return ModuleLink.objects.create(**validated_data)


class ModuleSerializer(ServcyDynamicBaseSerializer):
    member_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, allow_null=True
    )
    is_favorite = serializers.BooleanField(read_only=True)
    total_issues = serializers.IntegerField(read_only=True)
    cancelled_issues = serializers.IntegerField(read_only=True)
    completed_issues = serializers.IntegerField(read_only=True)
    started_issues = serializers.IntegerField(read_only=True)
    unstarted_issues = serializers.IntegerField(read_only=True)
    backlog_issues = serializers.IntegerField(read_only=True)

    class Meta:
        model = Module
        fields = [
            # Required fields
            "id",
            "workspace_id",
            "project_id",
            # Model fields
            "name",
            "description",
            "description_text",
            "description_html",
            "start_date",
            "target_date",
            "status",
            "lead_id",
            "member_ids",
            "view_props",
            "sort_order",
            # computed fields
            "is_favorite",
            "total_issues",
            "cancelled_issues",
            "completed_issues",
            "started_issues",
            "unstarted_issues",
            "backlog_issues",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ModuleDetailSerializer(ModuleSerializer):
    link_module = ModuleLinkSerializer(read_only=True, many=True)
    sub_issues = serializers.IntegerField(read_only=True)

    class Meta(ModuleSerializer.Meta):
        fields = ModuleSerializer.Meta.fields + ["link_module", "sub_issues"]


class ModuleFavoriteSerializer(ServcyBaseSerializer):
    module_detail = ModuleFlatSerializer(source="module", read_only=True)

    class Meta:
        model = ModuleFavorite
        fields = "__all__"
        read_only_fields = [
            "workspace",
            "project",
            "user",
        ]


class ModuleUserPropertiesSerializer(ServcyBaseSerializer):
    class Meta:
        model = ModuleUserProperties
        fields = "__all__"
        read_only_fields = ["workspace", "project", "module", "user"]
