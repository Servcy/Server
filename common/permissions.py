from rest_framework.permissions import SAFE_METHODS, BasePermission

from iam.enums import ERole
from iam.models import WorkspaceMember
from project.models import ProjectMember


class ProjectBasePermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        ## Safe Methods -> Handle the filtering logic in queryset
        if request.method in SAFE_METHODS:
            return WorkspaceMember.objects.filter(
                workspace__slug=view.workspace_slug,
                member=request.user,
                is_active=True,
            ).exists()

        ## Workspace guests cannot create projects
        if request.method == "POST":
            return (
                WorkspaceMember.objects.filter(
                    workspace__slug=view.workspace_slug,
                    member=request.user,
                    is_active=True,
                )
                .exclude(role=ERole.GUEST.value)
                .exists()
            )

        ## Only Project Admins can update project attributes
        return ProjectMember.objects.filter(
            workspace__slug=view.workspace_slug,
            member=request.user,
            role=ERole.ADMIN.value,
            project_id=view.project_id,
            is_active=True,
        ).exists()


class ProjectMemberPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        ## Safe Methods -> Handle the filtering logic in queryset
        if request.method in SAFE_METHODS:
            return ProjectMember.objects.filter(
                workspace__slug=view.workspace_slug,
                member=request.user,
                is_active=True,
            ).exists()

        ## Workspace guests cannot create projects
        if request.method == "POST":
            return (
                WorkspaceMember.objects.filter(
                    workspace__slug=view.workspace_slug,
                    member=request.user,
                    is_active=True,
                )
                .exclude(role=ERole.GUEST.value)
                .exists()
            )

        ## Guests cannot update project members
        return (
            ProjectMember.objects.filter(
                workspace__slug=view.workspace_slug,
                member=request.user,
                project_id=view.project_id,
                is_active=True,
            )
            .exclude(role=ERole.GUEST.value)
            .exists()
        )


class ProjectEntityPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        ## Safe Methods -> Handle the filtering logic in queryset
        if request.method in SAFE_METHODS:
            return ProjectMember.objects.filter(
                workspace__slug=view.workspace_slug,
                member=request.user,
                project_id=view.project_id,
                is_active=True,
            ).exists()

        ## Guests cannot create entities
        return (
            ProjectMember.objects.filter(
                workspace__slug=view.workspace_slug,
                member=request.user,
                project_id=view.project_id,
                is_active=True,
            )
            .exclude(role=ERole.GUEST.value)
            .exists()
        )


class ProjectLitePermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return ProjectMember.objects.filter(
            workspace__slug=view.workspace_slug,
            member=request.user,
            project_id=view.project_id,
            is_active=True,
        ).exists()


class WorkSpaceBasePermission(BasePermission):
    def has_permission(self, request, view):
        # Allow anyone to create a workspace
        if request.user.is_anonymous:
            return False

        if request.method == "POST":
            return True

        ## Safe Methods
        if request.method in SAFE_METHODS:
            return True

        # Only workspace admin can update the workspace
        if request.method in ["PUT", "PATCH"]:
            return WorkspaceMember.objects.filter(
                member=request.user,
                workspace__slug=view.workspace_slug,
                role=ERole.ADMIN.value,
                is_active=True,
            ).exists()

        # Allow workspace admin to delete the workspace
        if request.method == "DELETE":
            return WorkspaceMember.objects.filter(
                member=request.user,
                workspace__slug=view.workspace_slug,
                role=ERole.ADMIN.value,
                is_active=True,
            ).exists()


class WorkSpaceAdminPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return WorkspaceMember.objects.filter(
            member=request.user,
            workspace__slug=view.workspace_slug,
            role=ERole.ADMIN.value,
            is_active=True,
        ).exists()


class WorkspaceEntityPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        if request.method in SAFE_METHODS:
            return WorkspaceMember.objects.filter(
                workspace__slug=view.workspace_slug,
                member=request.user,
                is_active=True,
            ).exists()

        # Guests cannot create entities
        return (
            WorkspaceMember.objects.filter(
                member=request.user,
                workspace__slug=view.workspace_slug,
                is_active=True,
            )
            .exclude(role=ERole.GUEST.value)
            .exists()
        )


class WorkspaceViewerPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return WorkspaceMember.objects.filter(
            member=request.user,
            workspace__slug=view.workspace_slug,
            is_active=True,
        ).exists()


class WorkspaceUserPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return WorkspaceMember.objects.filter(
            member=request.user,
            workspace__slug=view.workspace_slug,
            is_active=True,
        ).exists()
