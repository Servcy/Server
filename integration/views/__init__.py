from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from integration.serializers import IntegrationSerializer


class IntegrationViewSet(ReadOnlyModelViewSet):
    serializer_class = IntegrationSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
