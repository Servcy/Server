import logging

from rest_framework.viewsets import GenericViewSet, mixins

from project.serializers import ProjectSerializer

logger = logging.getLogger(__name__)


class ProjectViewSet(
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class = ProjectSerializer
    queryset = ProjectSerializer.Meta.model.objects.all()
    ordering_fields = ["name"]

    def get_queryset(self):
        return super().get_queryset()
