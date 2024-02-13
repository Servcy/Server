import logging
import uuid

from rest_framework.viewsets import ModelViewSet

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
