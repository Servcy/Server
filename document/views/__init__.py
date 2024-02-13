import logging
import uuid

from rest_framework.viewsets import ModelViewSet

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
