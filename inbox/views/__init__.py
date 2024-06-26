import logging

from rest_framework import status
from rest_framework.decorators import action

from common.responses import error_response, success_response
from common.views import BaseViewSet
from inbox.services import InboxService

logger = logging.getLogger(__name__)


class InboxViewSet(BaseViewSet):
    @action(detail=False, methods=["post"], url_path="fetch")
    def fetch_items(self, request):
        try:
            user_id = request.user.id
            user = request.user
            inbox_service = InboxService(user=user, user_id=user_id)
            table_settings = request.data.get("pagination", {})
            items, details = inbox_service.get_paginated_items(
                filters=request.data.get("filters", {}),
                search=request.data.get("search", ""),
                sort_by=table_settings.get("sort_by", []),
                sort_desc=table_settings.get("sort_desc", []),
                page=table_settings.get("page", 1),
                page_size=table_settings.get("page_size", 10),
            )
            return success_response(
                results={
                    "items": items,
                    "details": details,
                },
                success_message="Inbox fetched successfully",
                status=status.HTTP_200_OK,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="Error while fetching inbox",
            )

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        try:
            user_id = request.user.id
            user = request.user
            inbox_service = InboxService(user=user, user_id=user_id)
            counts = inbox_service.get_unread_count()
            return success_response(
                results=counts,
                success_message="Unread count fetched successfully",
                status=status.HTTP_200_OK,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="Error while fetching unread count",
            )

    @action(detail=False, methods=["post"], url_path="read")
    def read_item(self, request):
        try:
            user_id = request.user.id
            user = request.user
            item_id = request.data.get("item_id")
            if not item_id:
                return error_response(
                    logger=logger,
                    logger_message="No item to read",
                )
            inbox_service = InboxService(user=user, user_id=user_id)
            inbox_service.read_item(item_id=item_id)
            return success_response(
                success_message="Inbox items read successfully",
                status=status.HTTP_200_OK,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="Error while reading inbox item",
            )

    @action(detail=False, methods=["post"], url_path="delete")
    def delete_items(self, request):
        try:
            user_id = request.user.id
            user = request.user
            item_ids = request.data.get("item_ids", [])
            if not item_ids:
                return error_response(
                    logger=logger,
                    logger_message="No items to delete",
                )
            inbox_service = InboxService(user=user, user_id=user_id)
            inbox_service.delete_items(item_ids=item_ids)
            return success_response(
                success_message="Inbox items deleted successfully",
                status=status.HTTP_200_OK,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="Error while deleting inbox items",
            )

    @action(detail=False, methods=["post"], url_path="archive")
    def archive_items(self, request):
        try:
            user_id = request.user.id
            user = request.user
            items_to_archive = request.data.get("item_ids", [])
            if not items_to_archive:
                return error_response(
                    logger=logger,
                    logger_message="No items to archive",
                )
            inbox_service = InboxService(user=user, user_id=user_id)
            inbox_service.archive_item(item_ids=items_to_archive)
            return success_response(
                success_message="Inbox items archived successfully",
                status=status.HTTP_200_OK,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="Error while archiving inbox items",
            )
