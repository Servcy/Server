import logging
import traceback
import uuid
from time import time

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet

from common.responses import error_response, success_response
from document.models import Document
from task.serializers import TaskSerializer

logger = logging.getLogger(__name__)


class TaskViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    queryset = TaskSerializer.Meta.model.objects.all()
    ordering_fields = ["name"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, uid=uuid.uuid4().hex)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        """Upload a file to the project"""
        try:
            files = request.FILES.getlist("file")
            user_id = request.user.id
            file_ids = []
            for file in files:
                file_name = file.name
                file.name = f"{user_id}_{file.name}_{int(time())}"
                task_document = Document.objects.create(
                    file=file,
                    user_id=user_id,
                    name=file_name,
                )
                file_ids.append(task_document.id)
            return success_response(
                results={"file_ids": file_ids},
                status=status.HTTP_201_CREATED,
            )
        except Exception as ex:
            logger.exception(
                f"An unexpected error occurred processing project file upload request",
                extra={
                    "traceback": traceback.format_exc(),
                },
            )
            return error_response(
                logger=logger,
                logger_message="An unexpected error occurred processing project file upload request.",
            )
