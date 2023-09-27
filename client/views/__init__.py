import logging
from time import time

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet

from client.models import Avatar
from client.serializers import ClientSerializer
from common.responses import error_response, success_response
from document.models import Document

logger = logging.getLogger(__name__)


class ClientViewSet(ModelViewSet):
    serializer_class = ClientSerializer
    queryset = ClientSerializer.Meta.model.objects.all()
    ordering_fields = ["name"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        """Upload a document for the client"""
        try:
            files = request.FILES.getlist("file")
            user_id = request.user.id
            file_ids = []
            for file in files:
                file_name = file.name
                file.name = f"{user_id}_{file.name}_{int(time())}"
                client_document = Document.objects.create(
                    file=file,
                    user_id=user_id,
                    name=file_name,
                )
                file_ids.append(client_document.id)
            return success_response(
                results={"file_ids": file_ids},
                status=status.HTTP_201_CREATED,
            )
        except Exception as ex:
            logger.exception(
                f"An unexpected error occurred processing client file upload request. {ex}"
            )
            return error_response(
                logger=logger,
                logger_message="An unexpected error occurred processing client file upload request.",
            )

    @action(detail=False, methods=["post"], url_path="avatar")
    def avatar(self, request):
        """Upload an Avatar for the client"""
        try:
            files = request.FILES.getlist("file")
            user_id = request.user.id
            for file in files:
                file.name = f"{user_id}_{file.name}_{int(time())}"
                avatar = Avatar.objects.create(
                    file=file,
                    user_id=user_id,
                )
                return success_response(
                    results={"avatar_id": avatar.id},
                    status=status.HTTP_201_CREATED,
                )
        except Exception as ex:
            logger.exception(
                f"An unexpected error occurred processing client avatar upload request. {ex}"
            )
            return error_response(
                logger=logger,
                logger_message="An unexpected error occurred processing client avatar upload request.",
            )
