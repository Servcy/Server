import logging
import time
import traceback
import uuid

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet

from common.responses import error_response, success_response
from document.repository import DocumentRepository
from document.serializers import DocumentSerializer

logger = logging.getLogger(__name__)


class DocumentViewSet(ModelViewSet):
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
            user_id = request.user.id
            file_ids = []
            for file in files:
                file_name = file.name
                file.name = f"{user_id}_{file.name}_{int(time())}"
                document = DocumentRepository.create(
                    file=file,
                    user_id=user_id,
                    name=file_name,
                    uid=uuid.uuid4().hex,
                )
                file_ids.append(document.id)
            return success_response(
                results={"file_ids": file_ids},
                status=status.HTTP_201_CREATED,
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
