from django.db import connection
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.gzip import gzip_page
from rest_framework import status
from rest_framework.response import Response

from common.permissions import ProjectEntityPermission
from common.views import BaseAPIView, BaseViewSet
from iam.enums import EAccess, ERole
from project.models import Page, PageFavorite, PageLog, ProjectMember
from project.serializers import (
    PageFavoriteSerializer,
    PageLogSerializer,
    PageSerializer,
    SubPageSerializer,
)


def unarchive_archive_page_and_descendants(page_id, archived_at):
    # TODO: Use Django ORM to update the page and its descendants
    # DANGER: This is a raw SQL query and should be used with caution
    sql = """
    WITH RECURSIVE descendants AS (
        SELECT id FROM page WHERE id = %s
        UNION ALL
        SELECT page.id FROM page, descendants WHERE page.parent_id = descendants.id
    )
    UPDATE page SET archived_at = %s WHERE id IN (SELECT id FROM descendants);
    """

    # Execute the SQL query
    with connection.cursor() as cursor:
        cursor.execute(sql, [page_id, archived_at])


class PageViewSet(BaseViewSet):
    serializer_class = PageSerializer
    model = Page
    permission_classes = [
        ProjectEntityPermission,
    ]
    search_fields = [
        "name",
    ]

    def get_queryset(self):
        subquery = PageFavorite.objects.filter(
            user=self.request.user,
            page_id=OuterRef("pk"),
            project_id=self.kwargs.get("project_id"),
            workspace__slug=self.kwargs.get("workspace_slug"),
        )
        return self.filter_queryset(
            super()
            .get_queryset()
            .filter(workspace__slug=self.kwargs.get("workspace_slug"))
            .filter(project_id=self.kwargs.get("project_id"))
            .filter(
                project__project_projectmember__member=self.request.user,
                project__archived_at__isnull=True,
                project__project_projectmember__is_active=True,
            )
            .filter(parent__isnull=True)
            .filter(Q(owned_by=self.request.user) | Q(access=EAccess.PUBLIC.value))
            .select_related("project")
            .select_related("workspace")
            .select_related("owned_by")
            .annotate(is_favorite=Exists(subquery))
            .order_by(self.request.GET.get("order_by", "-created_at"))
            .prefetch_related("labels")
            .order_by("-is_favorite", "-created_at")
            .distinct()
        )

    def create(self, request, workspace_slug, project_id):
        serializer = PageSerializer(
            data=request.data,
            context={"project_id": project_id, "owned_by_id": request.user.id},
        )

        if serializer.is_valid():
            serializer.save(
                created_by=self.request.user,
                updated_by=self.request.user,
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, workspace_slug, project_id, pk):
        try:
            page = Page.objects.get(
                pk=pk, workspace__slug=workspace_slug, project_id=project_id
            )

            if page.is_locked:
                return Response(
                    {"error": "Page is locked"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            parent = request.data.get("parent", None)
            if parent:
                _ = Page.objects.get(
                    pk=parent, workspace__slug=workspace_slug, project_id=project_id
                )

            if (
                page.access != request.data.get("access", page.access)
                and page.owned_by_id != request.user.id
            ):
                return Response(
                    {
                        "error": "Access cannot be updated since this page is owned by someone else"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = PageSerializer(page, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Page.DoesNotExist:
            return Response(
                {
                    "error": "Access cannot be updated since this page is owned by someone else"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def lock(self, request, workspace_slug, project_id, page_id):
        page = Page.objects.filter(
            pk=page_id, workspace__slug=workspace_slug, project_id=project_id
        ).first()

        page.is_locked = True
        page.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def unlock(self, request, workspace_slug, project_id, page_id):
        page = Page.objects.filter(
            pk=page_id, workspace__slug=workspace_slug, project_id=project_id
        ).first()

        page.is_locked = False
        page.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request, workspace_slug, project_id):
        queryset = self.get_queryset().filter(archived_at__isnull=True)
        pages = PageSerializer(queryset, many=True).data
        return Response(pages, status=status.HTTP_200_OK)

    def archive(self, request, workspace_slug, project_id, page_id):
        page = Page.objects.get(
            pk=page_id, workspace__slug=workspace_slug, project_id=project_id
        )

        if (
            ProjectMember.objects.filter(
                project_id=project_id,
                member=request.user,
                is_active=True,
                role=ERole.GUEST.value,
            ).exists()
            and request.user.id != page.owned_by_id
        ):
            return Response(
                {"error": "Guests cannot archive the page"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        unarchive_archive_page_and_descendants(page_id, timezone.now())

        return Response(status=status.HTTP_204_NO_CONTENT)

    def unarchive(self, request, workspace_slug, project_id, page_id):
        page = Page.objects.get(
            pk=page_id, workspace__slug=workspace_slug, project_id=project_id
        )

        if (
            ProjectMember.objects.filter(
                project_id=project_id,
                member=request.user,
                is_active=True,
                role=ERole.GUEST.value,
            ).exists()
            and request.user.id != page.owned_by_id
        ):
            return Response(
                {"error": "Guests cannot unarchive the page"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # if parent page is archived then the page will be un archived breaking the hierarchy
        if page.parent_id and page.parent.archived_at:
            page.parent = None
            page.save(update_fields=["parent"])

        unarchive_archive_page_and_descendants(page_id, None)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def archive_list(self, request, workspace_slug, project_id):
        pages = Page.objects.filter(
            project_id=project_id,
            workspace__slug=workspace_slug,
        ).filter(archived_at__isnull=False)

        pages = PageSerializer(pages, many=True).data
        return Response(pages, status=status.HTTP_200_OK)

    def destroy(self, request, workspace_slug, project_id, pk):
        page = Page.objects.get(
            pk=pk, workspace__slug=workspace_slug, project_id=project_id
        )

        if (
            ProjectMember.objects.filter(
                project_id=project_id,
                member=request.user,
                is_active=True,
                role=ERole.GUEST.value,
            ).exists()
            or request.user.id != page.owned_by_id
        ):
            return Response(
                {"error": "Guests cannot delete the page"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if page.archived_at is None:
            return Response(
                {"error": "The page should be archived before deleting"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # remove parent from all the children
        _ = Page.objects.filter(
            parent_id=pk, project_id=project_id, workspace__slug=workspace_slug
        ).update(parent=None)

        page.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PageFavoriteViewSet(BaseViewSet):
    permission_classes = [
        ProjectEntityPermission,
    ]

    serializer_class = PageFavoriteSerializer
    model = PageFavorite

    def get_queryset(self):
        return self.filter_queryset(
            super()
            .get_queryset()
            .filter(archived_at__isnull=True)
            .filter(workspace__slug=self.kwargs.get("workspace_slug"))
            .filter(user=self.request.user)
            .select_related("page", "page__owned_by")
        )

    def create(self, request, workspace_slug, project_id):
        serializer = PageFavoriteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                user=request.user,
                project_id=project_id,
                created_by=self.request.user,
                updated_by=self.request.user,
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, workspace_slug, project_id, page_id):
        page_favorite = PageFavorite.objects.get(
            project=project_id,
            user=request.user,
            workspace__slug=workspace_slug,
            page_id=page_id,
        )
        page_favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PageLogEndpoint(BaseAPIView):
    permission_classes = [
        ProjectEntityPermission,
    ]

    serializer_class = PageLogSerializer
    model = PageLog

    def post(self, request, workspace_slug, project_id, page_id):
        serializer = PageLogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                project_id=project_id,
                page_id=page_id,
                created_by=self.request.user,
                updated_by=self.request.user,
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, workspace_slug, project_id, page_id, transaction):
        page_transaction = PageLog.objects.get(
            workspace__slug=workspace_slug,
            project_id=project_id,
            page_id=page_id,
            transaction=transaction,
        )
        serializer = PageLogSerializer(
            page_transaction, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, workspace_slug, project_id, page_id, transaction):
        transaction = PageLog.objects.get(
            workspace__slug=workspace_slug,
            project_id=project_id,
            page_id=page_id,
            transaction=transaction,
        )
        # Delete the transaction object
        transaction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubPagesEndpoint(BaseAPIView):
    permission_classes = [
        ProjectEntityPermission,
    ]

    @method_decorator(gzip_page)
    def get(self, request, workspace_slug, project_id, page_id):
        pages = (
            PageLog.objects.filter(
                page_id=page_id,
                project_id=project_id,
                workspace__slug=workspace_slug,
                entity_name__in=["forward_link", "back_link"],
            )
            .select_related("project")
            .select_related("workspace")
        )
        return Response(
            SubPageSerializer(pages, many=True).data, status=status.HTTP_200_OK
        )
