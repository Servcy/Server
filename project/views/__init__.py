import logging

from rest_framework.viewsets import ModelViewSet

from project.serializers import ProjectSerializer
from project.models import ProjectFile
from rest_framework.decorators import action
from common.responses import error_response, success_response
from rest_framework import status

logger = logging.getLogger(__name__)


class ProjectViewSet(ModelViewSet):
    serializer_class = ProjectSerializer
    queryset = ProjectSerializer.Meta.model.objects.all()
    ordering_fields = ["name"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        """Upload a file to the project"""
        try:
            files = request.FILES.getlist("file")
            user_id = request.user.id
            file_ids = []
            for file in files:
                project_file = ProjectFile.objects.create(
                    file=file,
                    user_id=user_id,
                    name=file.name,
                )
                file_ids.append(project_file.id)
            return success_response(
                results={"file_ids": file_ids},
                status=status.HTTP_201_CREATED,
            )
        except Exception as ex:
            logger.exception(
                f"An unexpected error occurred processing project file upload request: {str(ex)}"
            )
            return error_response(
                logger=logger,
                logger_message="An unexpected error occurred processing project file upload request.",
            )
