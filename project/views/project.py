import jwt
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError
from django.db.models import Exists, F, Func, OuterRef, Prefetch, Q, Subquery
from django.utils import timezone
from rest_framework import serializers, status
from django.db import transaction
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from common.permissions import (
    ProjectBasePermission,
    ProjectLitePermission,
    ProjectMemberPermission,
    WorkspaceUserPermission,
)
from common.views import BaseAPIView, BaseViewSet
from iam.enums import EAccess, ERole
from iam.models import User, Workspace, WorkspaceMember
from common.states import DEFAULT_STATES
from project.models import (
    Cycle,
    IssueProperty,
    Module,
    Project,
    ProjectDeployBoard,
    ProjectFavorite,
    ProjectIdentifier,
    ProjectMember,
    ProjectMemberInvite,
    State,
)
from project.serializers import (
    ProjectDeployBoardSerializer,
    ProjectFavoriteSerializer,
    ProjectListSerializer,
    ProjectMemberAdminSerializer,
    ProjectMemberInviteSerializer,
    ProjectMemberRoleSerializer,
    ProjectMemberSerializer,
    ProjectSerializer,
)


class ProjectViewSet(BaseViewSet):
    serializer_class = ProjectListSerializer
    model = Project
    webhook_event = "project"

    permission_classes = [
        ProjectBasePermission,
    ]

    def get_queryset(self):
        sort_order = ProjectMember.objects.filter(
            member=self.request.user,
            project_id=OuterRef("pk"),
            workspace__slug=self.kwargs.get("workspace_slug"),
            is_active=True,
        ).values("sort_order")
        return self.filter_queryset(
            super()
            .get_queryset()
            .filter(workspace__slug=self.kwargs.get("workspace_slug"))
            .filter(
                Q(project_projectmember__member=self.request.user)
                | Q(access=EAccess.PUBLIC.value)
            )
            .select_related(
                "workspace",
                "workspace__owner",
                "default_assignee",
                "lead",
            )
            .annotate(
                is_favorite=Exists(
                    ProjectFavorite.objects.filter(
                        user=self.request.user,
                        project_id=OuterRef("pk"),
                        workspace__slug=self.kwargs.get("workspace_slug"),
                    )
                )
            )
            .annotate(
                is_member=Exists(
                    ProjectMember.objects.filter(
                        member=self.request.user,
                        project_id=OuterRef("pk"),
                        workspace__slug=self.kwargs.get("workspace_slug"),
                        is_active=True,
                    )
                )
            )
            .annotate(
                total_members=ProjectMember.objects.filter(
                    project_id=OuterRef("id"),
                    is_active=True,
                )
                .order_by()
                .annotate(count=Func(F("id"), function="Count"))
                .values("count")
            )
            .annotate(
                total_cycles=Cycle.objects.filter(project_id=OuterRef("id"))
                .order_by()
                .annotate(count=Func(F("id"), function="Count"))
                .values("count")
            )
            .annotate(
                total_modules=Module.objects.filter(project_id=OuterRef("id"))
                .order_by()
                .annotate(count=Func(F("id"), function="Count"))
                .values("count")
            )
            .annotate(
                member_role=ProjectMember.objects.filter(
                    project_id=OuterRef("pk"),
                    member_id=self.request.user.id,
                    is_active=True,
                ).values("role")
            )
            .annotate(
                is_deployed=Exists(
                    ProjectDeployBoard.objects.filter(
                        project_id=OuterRef("pk"),
                        workspace__slug=self.kwargs.get("workspace_slug"),
                    )
                )
            )
            .annotate(sort_order=Subquery(sort_order))
            .prefetch_related(
                Prefetch(
                    "project_projectmember",
                    queryset=ProjectMember.objects.filter(
                        workspace__slug=self.kwargs.get("workspace_slug"),
                        is_active=True,
                    ).select_related("member"),
                    to_attr="members_list",
                )
            )
            .distinct()
        )

    def list(self, request, workspace_slug):
        fields = [field for field in request.GET.get("fields", "").split(",") if field]
        projects = self.get_queryset().order_by("sort_order", "name")
        if request.GET.get("per_page", False) and request.GET.get("cursor", False):
            return self.paginate(
                request=request,
                queryset=(projects),
                on_results=lambda projects: ProjectListSerializer(
                    projects, many=True
                ).data,
            )
        projects = ProjectListSerializer(
            projects, many=True, fields=fields if fields else None
        ).data
        return Response(projects, status=status.HTTP_200_OK)

    def create(self, request, workspace_slug):
        try:
            workspace = Workspace.objects.get(slug=workspace_slug)

            serializer = ProjectSerializer(
                data={**request.data}, context={"workspace_id": workspace.id}
            )
            if serializer.is_valid():
                with transaction.atomic():
                    serializer.save()
                    # Add the user as Administrator to the project
                    ProjectMember.objects.create(
                        project_id=serializer.data["id"],
                        member=request.user,
                        role=ERole.ADMIN.value,
                    )
                    # Also create the issue property for the user
                    IssueProperty.objects.create(
                        project_id=serializer.data["id"],
                        user=request.user,
                    )
                    if serializer.data["lead"] is not None and str(
                        serializer.data["lead"]
                    ) != str(request.user.id):
                        ProjectMember.objects.create(
                            project_id=serializer.data["id"],
                            member_id=serializer.data["lead"],
                            role=ERole.ADMIN.value,
                        )
                        # Also create the issue property for the user
                        IssueProperty.objects.create(
                            project_id=serializer.data["id"],
                            user_id=serializer.data["lead"],
                        )
                    # Default states
                    State.objects.bulk_create(
                        [
                            State(
                                name=state["name"],
                                color=state["color"],
                                project=serializer.instance,
                                sequence=state["sequence"],
                                workspace=serializer.instance.workspace,
                                group=state["group"],
                                default=state.get("default", False),
                                created_by=request.user,
                            )
                            for state in DEFAULT_STATES
                        ]
                    )
                    project = (
                        self.get_queryset().filter(pk=serializer.data["id"]).first()
                    )
                    serializer = ProjectListSerializer(project)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        except IntegrityError as e:
            if "already exists" in str(e):
                return Response(
                    {"name": "The project name is already taken"},
                    status=status.HTTP_410_GONE,
                )
        except Workspace.DoesNotExist as e:
            return Response(
                {"error": "Workspace does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except serializers.ValidationError as e:
            return Response(
                {"identifier": "The project identifier is already taken"},
                status=status.HTTP_410_GONE,
            )

    def partial_update(self, request, workspace_slug, pk=None):
        try:
            workspace = Workspace.objects.get(slug=workspace_slug)

            project = Project.objects.get(pk=pk)

            serializer = ProjectSerializer(
                project,
                data={**request.data},
                context={"workspace_id": workspace.id},
                partial=True,
            )

            if serializer.is_valid():
                serializer.save()
                project = self.get_queryset().filter(pk=serializer.data["id"]).first()
                serializer = ProjectListSerializer(project)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except IntegrityError as e:
            if "already exists" in str(e):
                return Response(
                    {"name": "The project name is already taken"},
                    status=status.HTTP_410_GONE,
                )
        except (Project.DoesNotExist, Workspace.DoesNotExist):
            return Response(
                {"error": "Project does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except serializers.ValidationError as e:
            return Response(
                {"identifier": "The project identifier is already taken"},
                status=status.HTTP_410_GONE,
            )


class ProjectInvitationsViewset(BaseViewSet):
    serializer_class = ProjectMemberInviteSerializer
    model = ProjectMemberInvite

    search_fields = []

    permission_classes = [
        ProjectBasePermission,
    ]

    def get_queryset(self):
        return self.filter_queryset(
            super()
            .get_queryset()
            .filter(workspace__slug=self.kwargs.get("workspace_slug"))
            .filter(project_id=self.kwargs.get("project_id"))
            .select_related("project")
            .select_related("workspace", "workspace__owner")
        )

    def create(self, request, workspace_slug, project_id):
        emails = request.data.get("emails", [])

        # Check if email is provided
        if not emails:
            return Response(
                {"error": "Emails are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        requesting_user = ProjectMember.objects.get(
            workspace__slug=workspace_slug,
            project_id=project_id,
            member_id=request.user.id,
        )

        # Check if any invited user has an higher role
        if len(
            [
                email
                for email in emails
                if int(email.get("role", ERole.MEMBER.value)) > requesting_user.role
            ]
        ):
            return Response(
                {"error": "You cannot invite a user with higher role"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        workspace = Workspace.objects.get(slug=workspace_slug)

        project_invitations = []
        for email in emails:
            try:
                validate_email(email.get("email"))
                project_invitations.append(
                    ProjectMemberInvite(
                        email=email.get("email").strip().lower(),
                        project_id=project_id,
                        workspace_id=workspace.id,
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
                    )
                )
            except ValidationError:
                return Response(
                    {
                        "error": f"Invalid email - {email} provided a valid email address is required to send the invite"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Create workspace member invite
        project_invitations = ProjectMemberInvite.objects.bulk_create(
            project_invitations, batch_size=1, ignore_conflicts=True
        )
        current_site = request.META.get("HTTP_ORIGIN")

        # Send invitations
        for invitation in project_invitations:
            project_invitations.delay(
                invitation.email,
                project_id,
                invitation.token,
                current_site,
                request.user.email,
            )

        return Response(
            {
                "message": "Email sent successfully",
            },
            status=status.HTTP_200_OK,
        )


class UserProjectInvitationsViewset(BaseViewSet):
    serializer_class = ProjectMemberInviteSerializer
    model = ProjectMemberInvite

    def get_queryset(self):
        return self.filter_queryset(
            super()
            .get_queryset()
            .filter(email=self.request.user.email)
            .select_related("workspace", "workspace__owner", "project")
        )

    def create(self, request, workspace_slug):
        project_ids = request.data.get("project_ids", [])

        # Get the workspace user role
        workspace_member = WorkspaceMember.objects.get(
            member=request.user,
            workspace__slug=workspace_slug,
            is_active=True,
        )

        workspace_role = workspace_member.role
        workspace = workspace_member.workspace

        # If the user was already part of workspace
        _ = ProjectMember.objects.filter(
            workspace__slug=workspace_slug,
            project_id__in=project_ids,
            member=request.user,
        ).update(is_active=True)

        ProjectMember.objects.bulk_create(
            [
                ProjectMember(
                    project_id=project_id,
                    member=request.user,
                    role=(
                        ERole.ADMIN.value
                        if workspace_role >= ERole.ADMIN.value
                        else ERole.MEMBER.value
                    ),
                    workspace=workspace,
                    created_by=request.user,
                )
                for project_id in project_ids
            ],
            ignore_conflicts=True,
        )

        IssueProperty.objects.bulk_create(
            [
                IssueProperty(
                    project_id=project_id,
                    user=request.user,
                    workspace=workspace,
                    created_by=request.user,
                )
                for project_id in project_ids
            ],
            ignore_conflicts=True,
        )

        return Response(
            {"message": "Projects joined successfully"},
            status=status.HTTP_201_CREATED,
        )


class ProjectJoinEndpoint(BaseAPIView):
    permission_classes = [
        AllowAny,
    ]

    def post(self, request, workspace_slug, project_id, pk):
        project_invite = ProjectMemberInvite.objects.get(
            pk=pk,
            project_id=project_id,
            workspace__slug=workspace_slug,
        )

        email = request.data.get("email", "")

        if email == "" or project_invite.email != email:
            return Response(
                {"error": "You do not have permission to join the project"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if project_invite.responded_at is None:
            project_invite.accepted = request.data.get("accepted", False)
            project_invite.responded_at = timezone.now()
            project_invite.save()

            if project_invite.accepted:
                # Check if the user account exists
                user = User.objects.filter(email=email).first()

                # Check if user is a part of workspace
                workspace_member = WorkspaceMember.objects.filter(
                    workspace__slug=workspace_slug, member=user
                ).first()
                # Add him to workspace
                if workspace_member is None:
                    _ = WorkspaceMember.objects.create(
                        workspace_id=project_invite.workspace_id,
                        member=user,
                        role=(
                            ERole.ADMIN.value
                            if project_invite.role >= ERole.ADMIN.value
                            else project_invite.role
                        ),
                    )
                else:
                    # Else make him active
                    workspace_member.is_active = True
                    workspace_member.save()

                # Check if the user was already a member of project then activate the user
                project_member = ProjectMember.objects.filter(
                    workspace_id=project_invite.workspace_id, member=user
                ).first()
                if project_member is None:
                    # Create a Project Member
                    _ = ProjectMember.objects.create(
                        workspace_id=project_invite.workspace_id,
                        member=user,
                        role=project_invite.role,
                    )
                else:
                    project_member.is_active = True
                    project_member.role = project_member.role
                    project_member.save()

                return Response(
                    {"message": "Project Invitation Accepted"},
                    status=status.HTTP_200_OK,
                )

            return Response(
                {"message": "Project Invitation was not accepted"},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": "You have already responded to the invitation request"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get(self, request, workspace_slug, project_id, pk):
        project_invitation = ProjectMemberInvite.objects.get(
            workspace__slug=workspace_slug, project_id=project_id, pk=pk
        )
        serializer = ProjectMemberInviteSerializer(project_invitation)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProjectMemberViewSet(BaseViewSet):
    serializer_class = ProjectMemberAdminSerializer
    model = ProjectMember
    permission_classes = [
        ProjectMemberPermission,
    ]

    def get_permissions(self):
        if self.action == "leave":
            self.permission_classes = [
                ProjectLitePermission,
            ]
        else:
            self.permission_classes = [
                ProjectMemberPermission,
            ]

        return super(ProjectMemberViewSet, self).get_permissions()

    search_fields = [
        "member__display_name",
        "member__first_name",
    ]

    def get_queryset(self):
        return self.filter_queryset(
            super()
            .get_queryset()
            .filter(workspace__slug=self.kwargs.get("workspace_slug"))
            .filter(project_id=self.kwargs.get("project_id"))
            .filter()
            .select_related("project")
            .select_related("member")
            .select_related("workspace", "workspace__owner")
        )

    def create(self, request, workspace_slug, project_id):
        members = request.data.get("members", [])

        # get the project
        project = Project.objects.get(pk=project_id, workspace__slug=workspace_slug)

        if not len(members):
            return Response(
                {"error": "Atleast one member is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        bulk_project_members = []
        bulk_issue_props = []

        project_members = (
            ProjectMember.objects.filter(
                workspace__slug=workspace_slug,
                member_id__in=[member.get("member_id") for member in members],
            )
            .values("member_id", "sort_order")
            .order_by("sort_order")
        )

        bulk_project_members = []
        member_roles = {
            member.get("member_id"): member.get("role") for member in members
        }
        # Update roles in the members array based on the member_roles dictionary
        for project_member in ProjectMember.objects.filter(
            project_id=project_id,
            member_id__in=[member.get("member_id") for member in members],
        ):
            project_member.role = member_roles[str(project_member.member_id)]
            project_member.is_active = True
            bulk_project_members.append(project_member)

        # Update the roles of the existing members
        ProjectMember.objects.bulk_update(
            bulk_project_members, ["is_active", "role"], batch_size=100
        )

        for member in members:
            sort_order = [
                project_member.get("sort_order")
                for project_member in project_members
                if str(project_member.get("member_id")) == str(member.get("member_id"))
            ]
            bulk_project_members.append(
                ProjectMember(
                    member_id=member.get("member_id"),
                    role=member.get("role", ERole.MEMBER.value),
                    project_id=project_id,
                    workspace_id=project.workspace_id,
                    sort_order=sort_order[0] - 10000 if len(sort_order) else 65535,
                )
            )
            bulk_issue_props.append(
                IssueProperty(
                    user_id=member.get("member_id"),
                    project_id=project_id,
                    workspace_id=project.workspace_id,
                )
            )

        project_members = ProjectMember.objects.bulk_create(
            bulk_project_members,
            batch_size=10,
            ignore_conflicts=True,
        )

        IssueProperty.objects.bulk_create(
            bulk_issue_props, batch_size=10, ignore_conflicts=True
        )

        project_members = ProjectMember.objects.filter(
            project_id=project_id,
            member_id__in=[member.get("member_id") for member in members],
        )
        serializer = ProjectMemberRoleSerializer(project_members, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, workspace_slug, project_id):
        # Get the list of project members for the project
        project_members = ProjectMember.objects.filter(
            project_id=project_id,
            workspace__slug=workspace_slug,
            is_active=True,
        ).select_related("project", "member", "workspace")

        serializer = ProjectMemberRoleSerializer(
            project_members, fields=("id", "member", "role"), many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, workspace_slug, project_id, pk):
        project_member = ProjectMember.objects.get(
            pk=pk,
            workspace__slug=workspace_slug,
            project_id=project_id,
            is_active=True,
        )
        if request.user.id == project_member.member_id:
            return Response(
                {"error": "You cannot update your own role"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Check while updating user roles
        requested_project_member = ProjectMember.objects.get(
            project_id=project_id,
            workspace__slug=workspace_slug,
            member=request.user,
            is_active=True,
        )
        if (
            "role" in request.data
            and int(request.data.get("role", project_member.role))
            > requested_project_member.role
        ):
            return Response(
                {"error": "You cannot update a role that is higher than your own role"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ProjectMemberSerializer(
            project_member, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, workspace_slug, project_id, pk):
        project_member = ProjectMember.objects.get(
            workspace__slug=workspace_slug,
            project_id=project_id,
            pk=pk,
            is_active=True,
        )
        # check requesting user role
        requesting_project_member = ProjectMember.objects.get(
            workspace__slug=workspace_slug,
            member=request.user,
            project_id=project_id,
            is_active=True,
        )
        # User cannot remove himself
        if str(project_member.id) == str(requesting_project_member.id):
            return Response(
                {
                    "error": "You cannot remove yourself from the workspace. Please use leave workspace"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        # User cannot deactivate higher role
        if requesting_project_member.role < project_member.role:
            return Response(
                {"error": "You cannot remove a user having role higher than you"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        project_member.is_active = False
        project_member.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def leave(self, request, workspace_slug, project_id):
        project_member = ProjectMember.objects.get(
            workspace__slug=workspace_slug,
            project_id=project_id,
            member=request.user,
            is_active=True,
        )

        # Check if the leaving user is the only admin of the project
        if (
            project_member.role == ERole.ADMIN.value
            and not ProjectMember.objects.filter(
                workspace__slug=workspace_slug,
                project_id=project_id,
                role=ERole.ADMIN.value,
                is_active=True,
            ).count()
            > 1
        ):
            return Response(
                {
                    "error": "You cannot leave the project as your the only admin of the project you will have to either delete the project or create an another admin",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Deactivate the user
        project_member.is_active = False
        project_member.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectIdentifierEndpoint(BaseAPIView):
    permission_classes = [
        ProjectBasePermission,
    ]

    def get(self, request, workspace_slug):
        name = request.GET.get("name", "").strip().upper()

        if name == "":
            return Response(
                {"error": "Name is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        exists = ProjectIdentifier.objects.filter(
            name=name, workspace__slug=workspace_slug
        ).values("id", "name", "project")

        return Response(
            {"exists": len(exists), "identifiers": exists},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, workspace_slug):
        name = request.data.get("name", "").strip().upper()

        if name == "":
            return Response(
                {"error": "Name is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Project.objects.filter(
            identifier=name, workspace__slug=workspace_slug
        ).exists():
            return Response(
                {"error": "Cannot delete an identifier of an existing project"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ProjectIdentifier.objects.filter(
            name=name, workspace__slug=workspace_slug
        ).delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class ProjectUserViewsEndpoint(BaseAPIView):
    def post(self, request, workspace_slug, project_id):
        project = Project.objects.get(pk=project_id, workspace__slug=workspace_slug)

        project_member = ProjectMember.objects.filter(
            member=request.user,
            project=project,
            is_active=True,
        ).first()

        if project_member is None:
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        view_props = project_member.view_props
        default_props = project_member.default_props
        preferences = project_member.preferences
        sort_order = project_member.sort_order

        project_member.view_props = request.data.get("view_props", view_props)
        project_member.default_props = request.data.get("default_props", default_props)
        project_member.preferences = request.data.get("preferences", preferences)
        project_member.sort_order = request.data.get("sort_order", sort_order)

        project_member.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectMemberUserEndpoint(BaseAPIView):
    def get(self, request, workspace_slug, project_id):
        project_member = ProjectMember.objects.get(
            project_id=project_id,
            workspace__slug=workspace_slug,
            member=request.user,
            is_active=True,
        )
        serializer = ProjectMemberSerializer(project_member)

        return Response(serializer.data, status=status.HTTP_200_OK)


class ProjectFavoritesViewSet(BaseViewSet):
    serializer_class = ProjectFavoriteSerializer
    model = ProjectFavorite

    def get_queryset(self):
        return self.filter_queryset(
            super()
            .get_queryset()
            .filter(workspace__slug=self.kwargs.get("workspace_slug"))
            .filter(user=self.request.user)
            .select_related("project", "project__lead", "project__default_assignee")
            .select_related("workspace", "workspace__owner")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, workspace_slug):
        serializer = ProjectFavoriteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, workspace_slug, project_id):
        project_favorite = ProjectFavorite.objects.get(
            project=project_id, user=request.user, workspace__slug=workspace_slug
        )
        project_favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectDeployBoardViewSet(BaseViewSet):
    permission_classes = [
        ProjectMemberPermission,
    ]
    serializer_class = ProjectDeployBoardSerializer
    model = ProjectDeployBoard

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                workspace__slug=self.kwargs.get("workspace_slug"),
                project_id=self.kwargs.get("project_id"),
            )
            .select_related("project")
        )

    def create(self, request, workspace_slug, project_id):
        comments = request.data.get("comments", False)
        reactions = request.data.get("reactions", False)
        inbox = request.data.get("inbox", None)
        votes = request.data.get("votes", False)
        views = request.data.get(
            "views",
            {
                "list": True,
                "kanban": True,
                "calendar": True,
                "gantt": True,
                "spreadsheet": True,
            },
        )

        project_deploy_board, _ = ProjectDeployBoard.objects.get_or_create(
            anchor=f"{workspace_slug}/{project_id}",
            project_id=project_id,
        )
        project_deploy_board.comments = comments
        project_deploy_board.reactions = reactions
        project_deploy_board.inbox = inbox
        project_deploy_board.votes = votes
        project_deploy_board.views = views

        project_deploy_board.save()

        serializer = ProjectDeployBoardSerializer(project_deploy_board)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserProjectRolesEndpoint(BaseAPIView):
    permission_classes = [
        WorkspaceUserPermission,
    ]

    def get(self, request, workspace_slug):
        project_members = ProjectMember.objects.filter(
            workspace__slug=workspace_slug,
            member_id=request.user.id,
        ).values("project_id", "role")

        project_members = {
            str(member["project_id"]): member["role"] for member in project_members
        }
        return Response(project_members, status=status.HTTP_200_OK)
