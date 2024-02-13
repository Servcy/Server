import logging
import traceback
from time import time

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet

from client.repository.avatar import AvatarRepository
from client.serializers import ClientSerializer
from common.responses import error_response, success_response

logger = logging.getLogger(__name__)


class ClientViewSet(ModelViewSet):
    serializer_class = ClientSerializer
    queryset = ClientSerializer.Meta.model.objects.all()
    ordering_fields = ["name"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        serach = self.request.query_params.get("search", None)
        if serach:
            return self.queryset.filter(user=self.request.user, name__icontains=serach)
        return self.queryset.filter(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="avatar")
    def avatar(self, request):
        """Upload an Avatar for the client"""
        try:
            files = request.FILES.getlist("file")
            user_id = request.user.id
            for file in files:
                file.name = f"{user_id}_{file.name}_{int(time())}"
                avatar = AvatarRepository.create(
                    file=file,
                    user_id=user_id,
                )
                return success_response(
                    results={"avatar_id": avatar.id},
                    status=status.HTTP_201_CREATED,
                )
        except Exception:
            logger.exception(
                f"An unexpected error occurred processing client avatar upload request.",
                extra={
                    "traceback": traceback.format_exc(),
                },
            )
            return error_response(
                logger=logger,
                logger_message="An unexpected error occurred processing client avatar upload request.",
            )
