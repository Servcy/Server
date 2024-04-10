import logging

import jwt
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError
from django.db.models import Case, Count, F, Func, IntegerField, OuterRef, Q, When
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from common.permissions import (
    WorkSpaceAdminPermission,
    WorkSpaceBasePermission,
    WorkspaceEntityPermission,
    WorkspaceUserPermission,
)
from common.responses import error_response
from common.views import BaseAPIView, BaseViewSet
from iam.enums import ERole
from iam.models import User, Workspace, WorkspaceMember, WorkspaceMemberInvite
from iam.serializers import (
    UserReadSerializer,
    UserSerializer,
    UserSettingsSerializer,
    WorkspaceMemberAdminSerializer,
    WorkSpaceMemberInviteSerializer,
    WorkspaceMemberMeSerializer,
    WorkSpaceMemberSerializer,
    WorkSpaceSerializer,
)
from integration.repository import IntegrationRepository
from project.models import Issue, Project, ProjectMember, ProjectTemplate
from project.serializers import ProjectMemberSerializer

logger = logging.getLogger(__name__)


class UserEndpoint(BaseViewSet):
    serializer_class = UserSerializer
    model = User

    def get_object(self):
        return self.request.user

    def retrieve(self, request):
        serialized_data = UserReadSerializer(request.user).data
        return Response(
            serialized_data,
            status=status.HTTP_200_OK,
        )

    def retrieve_my_settings(self, request):
        serialized_data = UserSettingsSerializer(request.user).data
        return Response(serialized_data, status=status.HTTP_200_OK)

    def deactivate(self, request):
        # Check all workspace user is active
        user = self.get_object()
        projects_to_deactivate = []
        workspaces_to_deactivate = []
        projects = ProjectMember.objects.filter(
            member=request.user, is_active=True
        ).annotate(
            other_admin_exists=Count(
                Case(
                    When(
                        Q(role=ERole.ADMIN.value, is_active=True)
                        & ~Q(member=request.user),
                        then=1,
                    ),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
            total_members=Count("id"),
        )
        for project in projects:
            if project.other_admin_exists > 0 or (project.total_members == 1):
                project.is_active = False
                projects_to_deactivate.append(project)
            else:
                return Response(
                    {
                        "error": "You cannot deactivate account as you are the only admin in some projects."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        workspaces = WorkspaceMember.objects.filter(
            member=request.user, is_active=True
        ).annotate(
            other_admin_exists=Count(
                Case(
                    When(
                        Q(role=ERole.ADMIN.value, is_active=True)
                        & ~Q(member=request.user),
                        then=1,
                    ),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
            total_members=Count("id"),
        )
        for workspace in workspaces:
            if workspace.other_admin_exists > 0 or (workspace.total_members == 1):
                workspace.is_active = False
                workspaces_to_deactivate.append(workspace)
            else:
                return Response(
                    {
                        "error": "You cannot deactivate account as you are the only admin in some workspaces."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        ProjectMember.objects.bulk_update(
            projects_to_deactivate, ["is_active"], batch_size=100
        )
        WorkspaceMember.objects.bulk_update(
            workspaces_to_deactivate, ["is_active"], batch_size=100
        )
        IntegrationRepository.revoke_user_integrations(
            [],
            revoke_all=True,
            user_id=request.user.id,
        )
        user.is_active = False
        user.last_workspace_id = None
        user.is_tour_completed = False
        user.is_onboarded = False
        user.onboarding_step = {
            "workspace_join": False,
            "profile_complete": False,
            "workspace_create": False,
            "workspace_invite": False,
        }
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkSpaceViewSet(BaseViewSet):
    """
    This endpoint handles creating, listing, updating and deleting workspaces
    """

    model = Workspace
    serializer_class = WorkSpaceSerializer
    permission_classes = [
        WorkSpaceBasePermission,
    ]
    search_fields = [
        "name",
    ]
    filterset_fields = [
        "owner",
    ]
    lookup_field = "slug"

    @property
    def workspace_slug(self):
        return self.kwargs.get("slug", None)

    def get_queryset(self):
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
        return (
            self.filter_queryset(super().get_queryset().select_related("owner"))
            .order_by("name")
            .filter(
                workspace_member__member=self.request.user,
                workspace_member__is_active=True,
            )
            .annotate(total_members=member_count)
            .annotate(total_issues=issue_count)
            .select_related("owner")
        )

    def create(self, request):
        try:
            serializer = WorkSpaceSerializer(data=request.data)
            slug = request.data.get("slug", False)
            name = request.data.get("name", False)
            if not name or not slug:
                return Response(
                    {"error": "Both name and slug are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if len(name) > 80 and len(slug) > 48:
                return Response(
                    {"error": "The maximum length for name is 80 and for slug is 48"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if serializer.is_valid():
                serializer.save(
                    owner=request.user,
                    created_by=request.user,
                    updated_by=request.user,
                )
                WorkspaceMember.objects.create(
                    workspace_id=serializer.data["id"],
                    member=request.user,
                    role=ERole.ADMIN.value,
                    created_by=request.user,
                    updated_by=request.user,
                )
                ProjectTemplate.objects.create(
                    workspace_id=serializer.data["id"],
                    created_by=request.user,
                    updated_by=request.user,
                )
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(
                [serializer.errors[error][0] for error in serializer.errors],
                status=status.HTTP_400_BAD_REQUEST,
            )
        except IntegrityError as e:
            if "already exists" in str(e):
                return error_response(
                    "The workspace with the slug already exists",
                    logger=logger,
                    status=status.HTTP_410_GONE,
                )


class WorkspaceInvitationsViewset(BaseViewSet):
    """
    This endpoint handles creating, listing, updating and deleting workspace invitations
    """

    serializer_class = WorkSpaceMemberInviteSerializer
    model = WorkspaceMemberInvite

    permission_classes = [
        WorkSpaceAdminPermission,
    ]

    def get_queryset(self):
        return self.filter_queryset(
            super()
            .get_queryset()
            .filter(workspace__slug=self.kwargs.get("workspace_slug"))
            .select_related("workspace", "workspace__owner", "created_by")
        )

    def create(self, request, workspace_slug):
        emails = request.data.get("emails", [])
        if not emails:
            return Response(
                {"error": "Emails are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        workspace = Workspace.objects.get(slug=workspace_slug)
        workspace_members = WorkspaceMember.objects.filter(
            workspace=workspace,
            member__email__in=[email.get("email") for email in emails],
            is_active=True,
        ).select_related("member", "workspace", "workspace__owner")
        if workspace_members:
            return Response(
                {
                    "error": "Some users are already member of workspace",
                    "workspace_users": WorkSpaceMemberSerializer(
                        workspace_members, many=True
                    ).data,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        for email in emails:
            try:
                validate_email(email.get("email"))
                invite = WorkspaceMemberInvite(
                    email=email.get("email").strip().lower(),
                    workspace=workspace,
                    invited_by=request.user,
                    token=jwt.encode(
                        {
                            "email": email,
                            "timestamp": timezone.now().timestamp(),
                        },
                        settings.SECRET_KEY,
                        algorithm="HS256",
                    ),
                    role=email.get("role", ERole.MEMBER.value),
                    created_by=request.user,
                    updated_by=request.user,
                )
                invite.save()
            except ValidationError:
                return Response(
                    {
                        "error": f"Invalid email - {email} provided a valid email address is required to send the invite"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(
            {
                "message": "Invitations sent successfully!",
            },
            status=status.HTTP_200_OK,
        )

    def destroy(self, _, workspace_slug, pk):
        workspace_member_invite = WorkspaceMemberInvite.objects.get(
            pk=pk, workspace__slug=workspace_slug
        )
        workspace_member_invite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkspaceJoinEndpoint(BaseAPIView):
    """
    This endpoint handles:
    1. Joining a workspace
    2. Getting workspace invitation details
    """

    permission_classes = [
        AllowAny,
    ]

    def post(self, request, workspace_slug, pk):
        workspace_invite = WorkspaceMemberInvite.objects.get(
            pk=pk, workspace__slug=workspace_slug
        )

        email = request.data.get("email", "")

        # Check the email
        if email == "" or workspace_invite.email != email:
            return Response(
                {"error": "You do not have permission to join the workspace"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # If already responded then return error
        if workspace_invite.responded_at is None:
            workspace_invite.accepted = request.data.get("accepted", False)
            workspace_invite.responded_at = timezone.now()
            workspace_invite.save()

            if workspace_invite.accepted:
                # Check if the user created account after invitation
                user = User.objects.filter(email=email).first()

                # If the user is present then create the workspace member
                if user is not None:
                    # Check if the user was already a member of workspace then activate the user
                    workspace_member = WorkspaceMember.objects.filter(
                        workspace=workspace_invite.workspace, member=user
                    ).first()
                    if workspace_member is not None:
                        workspace_member.is_active = True
                        workspace_member.role = workspace_invite.role
                        workspace_member.save()
                    else:
                        # Create a Workspace
                        _ = WorkspaceMember.objects.create(
                            workspace=workspace_invite.workspace,
                            member=user,
                            role=workspace_invite.role,
                        )

                    # Set the user last_workspace_id to the accepted workspace
                    user.last_workspace_id = workspace_invite.workspace.id
                    user.save()

                    # Delete the invitation
                    workspace_invite.delete()

                return Response(
                    {"message": "Workspace Invitation Accepted"},
                    status=status.HTTP_200_OK,
                )

            # Workspace invitation rejected
            return Response(
                {"message": "Workspace Invitation was not accepted"},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": "You have already responded to the invitation request"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get(self, request, workspace_slug, pk):
        workspace_invitation = WorkspaceMemberInvite.objects.get(
            workspace__slug=workspace_slug, pk=pk
        )
        serializer = WorkSpaceMemberInviteSerializer(workspace_invitation)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserWorkspaceInvitationsViewSet(BaseViewSet):
    """
    This endpoint handles:
    1. Listing workspace invitations
    2. Accepting workspace invitations
    3. Rejecting workspace invitations
    """

    serializer_class = WorkSpaceMemberInviteSerializer
    model = WorkspaceMemberInvite

    def get_queryset(self):
        return self.filter_queryset(
            super()
            .get_queryset()
            .filter(email=self.request.user.email)
            .select_related("workspace", "workspace__owner", "created_by")
            .annotate(total_members=Count("workspace__workspace_member"))
        )

    def create(self, request):
        invitations = request.data.get("invitations", [])
        workspace_invitations = WorkspaceMemberInvite.objects.filter(
            pk__in=invitations, email=request.user.email
        ).order_by("-created_at")

        # If the user is already a member of workspace and was deactivated then activate the user
        for invitation in workspace_invitations:
            # Update the WorkspaceMember for this specific invitation
            WorkspaceMember.objects.filter(
                workspace_id=invitation.workspace_id, member=request.user
            ).update(is_active=True, role=invitation.role)

        # Bulk create the user for all the workspaces
        WorkspaceMember.objects.bulk_create(
            [
                WorkspaceMember(
                    workspace=invitation.workspace,
                    member=request.user,
                    role=invitation.role,
                    created_by=request.user,
                    updated_by=request.user,
                )
                for invitation in workspace_invitations
            ],
            ignore_conflicts=True,
        )

        # Delete joined workspace invites
        workspace_invitations.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkSpaceMemberViewSet(BaseViewSet):
    """
    This endpoint handles:
    1. Listing workspace members
    2. Updating workspace members
    3. Deleting workspace members
    4. Leaving a workspace
    """

    serializer_class = WorkspaceMemberAdminSerializer
    model = WorkspaceMember

    permission_classes = [
        WorkspaceEntityPermission,
    ]

    def get_permissions(self):
        if self.action == "leave":
            self.permission_classes = [
                WorkspaceUserPermission,
            ]
        else:
            self.permission_classes = [
                WorkspaceEntityPermission,
            ]

        return super(WorkSpaceMemberViewSet, self).get_permissions()

    search_fields = [
        "member__display_name",
        "member__first_name",
    ]

    def get_queryset(self):
        return self.filter_queryset(
            super()
            .get_queryset()
            .filter(
                workspace__slug=self.kwargs.get("workspace_slug"),
                is_active=True,
            )
            .select_related("workspace", "workspace__owner")
            .select_related("member")
        )

    def list(self, request, workspace_slug):
        workspace_member = WorkspaceMember.objects.get(
            member=request.user,
            workspace__slug=workspace_slug,
            is_active=True,
        )

        # Get all active workspace members
        workspace_members = self.get_queryset()

        if workspace_member.role > ERole.MEMBER.value:
            serializer = WorkspaceMemberAdminSerializer(
                workspace_members,
                fields=("id", "member", "role"),
                many=True,
            )
        else:
            serializer = WorkSpaceMemberSerializer(
                workspace_members,
                fields=("id", "member", "role"),
                many=True,
            )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, workspace_slug, pk):
        workspace_member = WorkspaceMember.objects.get(
            pk=pk,
            workspace__slug=workspace_slug,
            is_active=True,
        )
        if request.user.id == workspace_member.member_id:
            return Response(
                {"error": "You cannot update your own role"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get the requested user role
        requested_workspace_member = WorkspaceMember.objects.get(
            workspace__slug=workspace_slug,
            member=request.user,
            is_active=True,
        )
        # Check if role is being updated
        # One cannot update role higher than his own role
        if (
            "role" in request.data
            and int(request.data.get("role", workspace_member.role))
            > requested_workspace_member.role
        ):
            return Response(
                {"error": "You cannot update a role that is higher than your own role"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = WorkSpaceMemberSerializer(
            workspace_member, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save(
                updated_by=request.user,
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, workspace_slug, pk):
        # Check the user role who is deleting the user
        workspace_member = WorkspaceMember.objects.get(
            pk=pk,
            workspace__slug=workspace_slug,
            is_active=True,
        )

        # check requesting user role
        requesting_workspace_member = WorkspaceMember.objects.get(
            workspace__slug=workspace_slug,
            member=request.user,
            is_active=True,
        )

        if str(workspace_member.id) == str(requesting_workspace_member.id):
            return Response(
                {
                    "error": "You cannot remove yourself from the workspace. Please use leave workspace"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if requesting_workspace_member.role < workspace_member.role:
            return Response(
                {"error": "You cannot remove a user having role higher than you"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            Project.objects.annotate(
                total_members=Count("project_projectmember"),
                member_with_role=Count(
                    "project_projectmember",
                    filter=Q(
                        project_projectmember__member_id=workspace_member.id,
                        project_projectmember__role=ERole.ADMIN.value,
                    ),
                ),
            )
            .filter(total_members=1, member_with_role=1, workspace__slug=workspace_slug)
            .exists()
        ):
            return Response(
                {
                    "error": "User is a part of some projects where they are the only admin, they should either leave that project or promote another user to admin."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Deactivate the users from the projects where the user is part of
        _ = ProjectMember.objects.filter(
            workspace__slug=workspace_slug,
            member_id=workspace_member.member_id,
            is_active=True,
        ).update(is_active=False)

        workspace_member.is_active = False
        workspace_member.updated_by = request.user
        workspace_member.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def leave(self, request, workspace_slug):
        workspace_member = WorkspaceMember.objects.get(
            workspace__slug=workspace_slug,
            member=request.user,
            is_active=True,
        )

        # Check if the leaving user is the only admin of the workspace
        if (
            workspace_member.role == ERole.ADMIN.value
            and not WorkspaceMember.objects.filter(
                workspace__slug=workspace_slug,
                role=ERole.ADMIN.value,
                is_active=True,
            ).count()
            > 1
        ):
            return Response(
                {
                    "error": "You cannot leave the workspace as you are the only admin of the workspace you will have to either delete the workspace or promote another user to admin."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            Project.objects.annotate(
                total_members=Count("project_projectmember"),
                member_with_role=Count(
                    "project_projectmember",
                    filter=Q(
                        project_projectmember__member_id=request.user.id,
                        project_projectmember__role=ERole.ADMIN.value,
                    ),
                ),
            )
            .filter(total_members=1, member_with_role=1, workspace__slug=workspace_slug)
            .exists()
        ):
            return Response(
                {
                    "error": "You are a part of some projects where you are the only admin, you should either leave the project or promote another user to admin."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # # Deactivate the users from the projects where the user is part of
        _ = ProjectMember.objects.filter(
            workspace__slug=workspace_slug,
            member_id=workspace_member.member_id,
            is_active=True,
        ).update(is_active=False)

        # # Deactivate the user
        workspace_member.is_active = False
        workspace_member.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserLastProjectWithWorkspaceEndpoint(BaseAPIView):
    """
    This endpoint returns the last workspace and project in which the user was involved
    """

    def get(self, request):
        user = User.objects.get(pk=request.user.id)

        last_workspace_id = user.last_workspace_id

        if last_workspace_id is None:
            return Response(
                {
                    "project_details": [],
                    "workspace_details": {},
                },
                status=status.HTTP_200_OK,
            )

        workspace = Workspace.objects.get(pk=last_workspace_id)
        workspace_serializer = WorkSpaceSerializer(workspace)

        project_member = ProjectMember.objects.filter(
            workspace_id=last_workspace_id, member=request.user
        ).select_related("workspace", "project", "member", "workspace__owner")

        project_member_serializer = ProjectMemberSerializer(project_member, many=True)

        return Response(
            {
                "workspace_details": workspace_serializer.data,
                "project_details": project_member_serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class WorkspaceMemberUserEndpoint(BaseAPIView):
    """
    This endpoint returns the workspace member details of the user
    """

    def get(self, request, workspace_slug):
        workspace_member = WorkspaceMember.objects.get(
            member=request.user,
            workspace__slug=workspace_slug,
            is_active=True,
        )
        serializer = WorkspaceMemberMeSerializer(workspace_member)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WorkspaceMemberUserViewsEndpoint(BaseAPIView):
    """
    This endpoint returns the workspace member views of the user
    """

    def post(self, request, workspace_slug):
        workspace_member = WorkspaceMember.objects.get(
            workspace__slug=workspace_slug,
            member=request.user,
            is_active=True,
        )
        workspace_member.view_props = request.data.get("view_props", {})
        workspace_member.updated_by = request.user
        workspace_member.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkSpaceAvailabilityCheckEndpoint(BaseAPIView):
    def get(self, request):
        slug = request.GET.get("slug", False)

        if not slug or slug == "":
            return Response(
                {"error": "Workspace Slug is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        workspace = Workspace.objects.filter(slug=slug).exists()
        return Response({"status": not workspace}, status=status.HTTP_200_OK)


class UpdateUserOnBoardedEndpoint(BaseAPIView):
    def patch(self, request):
        user = User.objects.get(pk=request.user.id, is_active=True)
        user.is_onboarded = request.data.get("is_onboarded", False)
        user.save()
        return Response({"message": "Updated successfully"}, status=status.HTTP_200_OK)


class UpdateUserTourCompletedEndpoint(BaseAPIView):
    def patch(self, request):
        user = User.objects.get(pk=request.user.id, is_active=True)
        user.is_tour_completed = request.data.get("is_tour_completed", False)
        user.save()
        return Response({"message": "Updated successfully"}, status=status.HTTP_200_OK)
