from rest_framework.permissions import SAFE_METHODS, BasePermission

from iam.models import WorkspaceMember
from project.models import ProjectMember

Member = 1
Guest = 0
Admin = 2
Owner = 3


class ProjectBasePermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        ## Safe Methods -> Handle the filtering logic in queryset
        if request.method in SAFE_METHODS:
            return WorkspaceMember.objects.filter(
                workspace__slug=view.workspace__slug,
                member=request.user,
                is_active=True,
            ).exists()

        ## Only workspace owners or admins can create the projects
        if request.method == "POST":
            return WorkspaceMember.objects.filter(
                workspace__slug=view.workspace__slug,
                member=request.user,
                role__in=[Admin, Member],
                is_active=True,
            ).exists()

        ## Only Project Admins can update project attributes
        return ProjectMember.objects.filter(
            workspace__slug=view.workspace__slug,
            member=request.user,
            role=Admin,
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
                workspace__slug=view.workspace__slug,
                member=request.user,
                is_active=True,
            ).exists()
        ## Only workspace owners or admins can create the projects
        if request.method == "POST":
            return WorkspaceMember.objects.filter(
                workspace__slug=view.workspace__slug,
                member=request.user,
                role__in=[Admin, Member],
                is_active=True,
            ).exists()

        ## Only Project Admins can update project attributes
        return ProjectMember.objects.filter(
            workspace__slug=view.workspace__slug,
            member=request.user,
            role__in=[Admin, Member],
            project_id=view.project_id,
            is_active=True,
        ).exists()


class ProjectEntityPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        ## Safe Methods -> Handle the filtering logic in queryset
        if request.method in SAFE_METHODS:
            return ProjectMember.objects.filter(
                workspace__slug=view.workspace__slug,
                member=request.user,
                project_id=view.project_id,
                is_active=True,
            ).exists()

        ## Only project members or admins can create and edit the project attributes
        return ProjectMember.objects.filter(
            workspace__slug=view.workspace__slug,
            member=request.user,
            role__in=[Admin, Member],
            project_id=view.project_id,
            is_active=True,
        ).exists()


class ProjectLitePermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return ProjectMember.objects.filter(
            workspace__slug=view.workspace__slug,
            member=request.user,
            project_id=view.project_id,
            is_active=True,
        ).exists()


class WorkSpaceBasePermission(BasePermission):
    def has_permission(self, request, view):
        # allow anyone to create a workspace
        if request.user.is_anonymous:
            return False

        if request.method == "POST":
            return True

        ## Safe Methods
        if request.method in SAFE_METHODS:
            return True

        # allow only admins and owners to update the workspace settings
        if request.method in ["PUT", "PATCH"]:
            return WorkspaceMember.objects.filter(
                member=request.user,
                workspace__slug=view.workspace__slug,
                role__in=[Owner, Admin],
                is_active=True,
            ).exists()

        # allow only owner to delete the workspace
        if request.method == "DELETE":
            return WorkspaceMember.objects.filter(
                member=request.user,
                workspace__slug=view.workspace__slug,
                role=Owner,
                is_active=True,
            ).exists()


class WorkspaceOwnerPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return WorkspaceMember.objects.filter(
            workspace__slug=view.workspace__slug,
            member=request.user,
            role=Owner,
        ).exists()


class WorkSpaceAdminPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return WorkspaceMember.objects.filter(
            member=request.user,
            workspace__slug=view.workspace__slug,
            role__in=[Owner, Admin],
            is_active=True,
        ).exists()


class WorkspaceEntityPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        if request.method in SAFE_METHODS:
            return WorkspaceMember.objects.filter(
                workspace__slug=view.workspace__slug,
                member=request.user,
                is_active=True,
            ).exists()

        return WorkspaceMember.objects.filter(
            member=request.user,
            workspace__slug=view.workspace__slug,
            role__in=[Owner, Admin],
            is_active=True,
        ).exists()


class WorkspaceViewerPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return WorkspaceMember.objects.filter(
            member=request.user,
            workspace__slug=view.workspace__slug,
            is_active=True,
        ).exists()


class WorkspaceUserPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return WorkspaceMember.objects.filter(
            member=request.user,
            workspace__slug=view.workspace__slug,
            is_active=True,
        ).exists()
