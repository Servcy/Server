import logging
import uuid

from rest_framework.viewsets import ModelViewSet

from project.serializers import ProjectSerializer

logger = logging.getLogger(__name__)


class ProjectViewSet(ModelViewSet):
    serializer_class = ProjectSerializer
    queryset = ProjectSerializer.Meta.model.objects.all()
    ordering_fields = ["name"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, uid=uuid.uuid4().hex)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
