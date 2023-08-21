import logging

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet

from common.responses import error_response, success_response
from inbox.services import InboxService

logger = logging.getLogger(__name__)


class InboxViewSet(ViewSet):
    @action(detail=False, methods=["get"], url_path="sync")
    def sync_inbox(self, request):
        try:
            user_id = request.user.id
            inbox_service = InboxService(user_id=user_id)
            return success_response(
                results=inbox_service.sync_inbox(),
                success_message="Inbox synced successfully.",
                status=status.HTTP_200_OK,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="An error occurred while syncing inbox.",
            )
