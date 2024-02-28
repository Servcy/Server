import logging

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet

from common.responses import error_response, success_response
from inbox.repository import InboxRepository
from inbox.services import InboxService

logger = logging.getLogger(__name__)


class InboxViewSet(ViewSet):
    @action(detail=False, methods=["post"], url_path="items")
    def fetch_items(self, request):
        try:
            user_id = request.user.id
            user = request.user
            inbox_service = InboxService(user=user, user_id=user_id)
            table_settings = request.data.get("pagination", {})
            items, details = inbox_service.get_paginated_items(
                filters=request.data.get("filters", {}),
                search=request.data.get("search", {}),
                sort_by=table_settings.get("sort_by", []),
                sort_desc=table_settings.get("sort_desc", []),
                page=table_settings.get("page", 1),
                page_size=table_settings.get("page_size", 50),
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

    @action(detail=False, methods=["post"], url_path="block-email")
    def block_email(self, request):
        try:
            user = request.user
            email = request.data.get("email")
            if not email:
                return error_response(
                    logger=logger,
                    logger_message="No email to block!",
                )
            InboxRepository.block_email(email=email, user=user)
            return success_response(
                success_message="Email blocked successfully",
                status=status.HTTP_200_OK,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="Error while blocking email",
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
