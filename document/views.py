import logging
import traceback
from time import time

import requests
from django.conf import settings
from rest_framework.decorators import action
from rest_framework.response import Response

from common.responses import error_response
from common.views import BaseAPIView, BaseViewSet
from document.repository import DocumentRepository
from document.serializers import DocumentSerializer

logger = logging.getLogger(__name__)


class DocumentViewSet(BaseViewSet):
    """
    DocumentViewSet allows to perform CRUD operations on Document model
    """

    serializer_class = DocumentSerializer
    queryset = DocumentSerializer.Meta.model.objects.all()
    ordering_fields = ["name"]

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def get_queryset(self):
        serach = self.request.query_params.get("search", None)
        queryset = self.queryset.filter(created_by=self.request.user)
        if serach:
            queryset = queryset.filter(name__icontains=serach)
        return queryset

    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        """Upload a document"""
        try:
            files = request.FILES.getlist("file")
            meta_data = request.data.get("meta_data", {})
            workspace_id = request.data.get("workspace_id", None)
            if workspace_id and workspace_id != "null" and workspace_id != "undefined":
                workspace_id = int(workspace_id)
            user_id = request.user.id
            file_data = []
            for file in files:
                file_name = file.name
                file.name = f"{user_id}_{file.name}_{int(time())}"
                document = DocumentRepository.add_document(
                    file=file,
                    meta_data=meta_data,
                    created_by_id=user_id,
                    updated_by_id=user_id,
                    workspace_id=workspace_id,
                    name=file_name,
                )
                file_data.append(
                    {
                        "url": document.file.url,
                        "id": document.id,
                    }
                )
            return Response(file_data[0]) if len(files) == 1 else Response(file_data)
        except ValueError:
            logger.exception(
                f"An unexpected error occurred processing the request",
                extra={
                    "traceback": traceback.format_exc(),
                },
            )
            return error_response(
                logger=logger,
                logger_message="An unexpected error occurred processing the request",
                error_message="Invalid request data",
                status=400,
            )
        except Exception:
            logger.exception(
                f"An unexpected error occurred processing the request",
                extra={
                    "traceback": traceback.format_exc(),
                },
            )
            return error_response(
                logger=logger,
                logger_message="An unexpected error occurred processing the request",
            )

    @action(detail=False, methods=["post"], url_path="delete")
    def delete(self, request):
        instance = DocumentRepository.get_document(
            {
                "file": request.data.get("file"),
            }
        )
        instance.is_deleted = True
        instance.updated_by = request.user
        instance.save()
        return Response(status=204)

    @action(detail=False, methods=["post"], url_path="restore")
    def restore(self, request):
        instance = DocumentRepository.get_document(
            {
                "file": request.data.get("file"),
            }
        )
        instance.is_deleted = False
        instance.updated_by = request.user
        instance.save()
        return Response(status=200)


class UnsplashEndpoint(BaseAPIView):
    def get(self, request):
        query = request.GET.get("query", False)
        page = request.GET.get("page", 1)
        per_page = request.GET.get("per_page", 20)

        url = (
            f"https://api.unsplash.com/search/photos/?client_id={settings.UNSPLASH_ACCESS_KEY}&query={query}&page=${page}&per_page={per_page}"
            if query
            else f"https://api.unsplash.com/photos/?client_id={settings.UNSPLASH_ACCESS_KEY}&page={page}&per_page={per_page}"
        )
        headers = {
            "Content-Type": "application/json",
        }
        resp = requests.get(url=url, headers=headers)
        return Response(resp.json(), status=resp.status_code)
