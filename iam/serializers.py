from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from app.serializers import ServcyBaseSerializer, ServcyDynamicBaseSerializer
from common.validators import INVALID_SLUGS
from iam.models import User, Workspace, WorkspaceMember, WorkspaceMemberInvite


class JWTTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["id"] = user.id
        token["email"] = user.email
        token["username"] = user.username
        token["phone_number"] = user.phone_number
        token["invited_by"] = user.invited_by.id if user.invited_by else None
        return token


class UserSerializer(ServcyBaseSerializer):
    class Meta:
        model = User
        fields = "__all__"
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "is_superuser",
            "is_staff",
            "is_onboarded",
        ]
        extra_kwargs = {"password": {"write_only": True}}

        def get_is_onboarded(self, obj):
            """If the user has already filled first name or last name then he is onboarded"""
            return bool(obj.first_name) or bool(obj.last_name)


class UserReadSerializer(ServcyBaseSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "avatar",
            "cover_image",
            "created_at",
            "display_name",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_onboarded",
            "is_tour_completed",
            "phone_number",
            "onboarding_step",
            "user_timezone",
            "username",
            "theme",
            "last_workspace_id",
            "use_case",
        ]
        read_only_fields = fields


class UserSettingsSerializer(ServcyBaseSerializer):
    workspace = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "workspace",
        ]
        read_only_fields = fields

    def get_workspace(self, obj):
        workspace_invites = WorkspaceMemberInvite.objects.filter(
            email=obj.email
        ).count()
        if (
            obj.last_workspace_id is not None
            and Workspace.objects.filter(
                pk=obj.last_workspace_id,
                workspace_member__member=obj.id,
                workspace_member__is_active=True,
            ).exists()
        ):
            workspace = Workspace.objects.filter(
                pk=obj.last_workspace_id,
                workspace_member__member=obj.id,
                workspace_member__is_active=True,
            ).first()
            return {
                "last_workspace_id": obj.last_workspace_id,
                "last_workspace_slug": workspace.slug if workspace is not None else "",
                "fallback_workspace_id": obj.last_workspace_id,
                "fallback_workspace_slug": (
                    workspace.slug if workspace is not None else ""
                ),
                "invites": workspace_invites,
            }
        else:
            fallback_workspace = (
                Workspace.objects.filter(
                    workspace_member__member_id=obj.id,
                    workspace_member__is_active=True,
                )
                .order_by("created_at")
                .first()
            )
            return {
                "last_workspace_id": None,
                "last_workspace_slug": None,
                "fallback_workspace_id": (
                    fallback_workspace.id if fallback_workspace is not None else None
                ),
                "fallback_workspace_slug": (
                    fallback_workspace.slug if fallback_workspace is not None else None
                ),
                "invites": workspace_invites,
            }


class UserLiteSerializer(ServcyBaseSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "display_name",
            "avatar",
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
            "display_name",
            "last_name",
            "email",
            "avatar",
        ]
        read_only_fields = [
            "id",
        ]


class WorkSpaceSerializer(ServcyDynamicBaseSerializer):
    owner = UserLiteSerializer(read_only=True)
    total_members = serializers.IntegerField(read_only=True)
    total_issues = serializers.IntegerField(read_only=True)

    def validated(self, data):
        if data.get("slug") in INVALID_SLUGS:
            raise serializers.ValidationError({"slug": "Slug is not valid"})

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
            "slug",
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
        model = WorkspaceMemberInvite
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
