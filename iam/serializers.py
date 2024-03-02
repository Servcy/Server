from rest_framework import serializers

from app.serializers import ServcyBaseSerializer, ServcyDynamicBaseSerializer
from iam.models import (
    User,
    Workspace,
    WorkspaceInvite,
    WorkspaceMember,
    WorkspaceTheme,
    WorkspaceUserProperties,
)


class UserLiteSerializer(ServcyBaseSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "profile_image",
        ]
        read_only_fields = [
            "id",
        ]


class UserAdminLiteSerializer(ServcyBaseSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "profile_image",
        ]
        read_only_fields = [
            "id",
        ]


class WorkSpaceSerializer(ServcyDynamicBaseSerializer):
    owner = UserLiteSerializer(read_only=True)
    total_members = serializers.IntegerField(read_only=True)
    total_issues = serializers.IntegerField(read_only=True)

    class Meta:
        model = Workspace
        fields = "__all__"
        read_only_fields = [
            "id",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            "owner",
        ]


class WorkspaceLiteSerializer(ServcyBaseSerializer):
    class Meta:
        model = Workspace
        fields = [
            "name",
            "id",
        ]
        read_only_fields = fields


class WorkSpaceMemberSerializer(ServcyDynamicBaseSerializer):
    member = UserLiteSerializer(read_only=True)
    workspace = WorkspaceLiteSerializer(read_only=True)

    class Meta:
        model = WorkspaceMember
        fields = "__all__"


class WorkspaceMemberMeSerializer(ServcyBaseSerializer):
    class Meta:
        model = WorkspaceMember
        fields = "__all__"


class WorkspaceMemberAdminSerializer(ServcyDynamicBaseSerializer):
    member = UserAdminLiteSerializer(read_only=True)
    workspace = WorkspaceLiteSerializer(read_only=True)

    class Meta:
        model = WorkspaceMember
        fields = "__all__"


class WorkSpaceMemberInviteSerializer(ServcyBaseSerializer):
    workspace = WorkSpaceSerializer(read_only=True)
    total_members = serializers.IntegerField(read_only=True)
    created_by_detail = UserLiteSerializer(read_only=True, source="created_by")

    class Meta:
        model = WorkspaceInvite
        fields = "__all__"
        read_only_fields = [
            "id",
            "email",
            "token",
            "workspace",
            "message",
            "created_at",
            "updated_at",
        ]


class WorkspaceThemeSerializer(ServcyBaseSerializer):
    class Meta:
        model = WorkspaceTheme
        fields = "__all__"
        read_only_fields = [
            "workspace",
            "actor",
        ]


class WorkspaceUserPropertiesSerializer(ServcyBaseSerializer):
    class Meta:
        model = WorkspaceUserProperties
        fields = "__all__"
        read_only_fields = [
            "workspace",
            "user",
        ]
