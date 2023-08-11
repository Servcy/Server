from rest_framework import viewsets
from rest_framework.decorators import action


class GoogleViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["get", "post"], url_path="oauth")
    def oauth(self, request):
        pass
