import logging
import traceback

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

logger = logging.getLogger(__name__)


class InboxViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="sync")
    def sync_inbox(self, request):
        try:
            pass
        except Exception:
            logger.error(
                f"An error occurred while inbox sync.\n{traceback.format_exc()}"
            )
            return Response(
                {"detail": "An error occurred. Please try again later!"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
