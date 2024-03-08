import logging
import traceback
import uuid
from time import time

import requests
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from common.responses import error_response, success_response
from common.views import BaseAPIView
from document.repository import DocumentRepository
from document.serializers import DocumentSerializer

logger = logging.getLogger(__name__)


class DocumentViewSet(ModelViewSet):
    """
    DocumentViewSet allows to perform CRUD operations on Document model
    """

    serializer_class = DocumentSerializer
    queryset = DocumentSerializer.Meta.model.objects.all()
    ordering_fields = ["name"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, uid=uuid.uuid4().hex)

    def get_queryset(self):
        serach = self.request.query_params.get("search", None)
        queryset = self.queryset.filter(user=self.request.user)
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


class UnsplashEndpoint(BaseAPIView):
    _unspalsh_url = "https://api.unsplash.com"
    _access_key = settings.UNSPLASH_ACCESS_KEY

    def get(self, request):
        query = request.GET.get("query", False)
        page = request.GET.get("page", 1)
        per_page = request.GET.get("per_page", 20)

        url = (
            f"https://api.unsplash.com/search/photos/?client_id={self._access_key}&query={query}&page=${page}&per_page={per_page}"
            if query
            else f"https://api.unsplash.com/photos/?client_id={self._access_key}&page={page}&per_page={per_page}"
        )
        headers = {
            "Content-Type": "application/json",
        }
        resp = requests.get(url=url, headers=headers)
        return Response(resp.json(), status=resp.status_code)
