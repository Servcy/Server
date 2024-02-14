import logging

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet

from common.responses import error_response, success_response
from document.repository import DocumentRepository
from inbox.services import InboxService
from integration.repository import IntegrationRepository
from integration.utils.maps import integration_service_map

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

    @action(detail=False, methods=["post"], url_path="read")
    def read_item(self, request):
        try:
            user_id = request.user.id
            user = request.user
            item_id = request.data.get("item_id", [])
            if not item_id:
                return error_response(
                    logger=logger,
                    logger_message="No items to archive",
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
                logger_message="Error while archiving inbox items",
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

    @action(methods=["post"], detail=False, url_path="send-reply")
    def send_reply(self, request):
        try:
            requesting_user = request.user
            body = request.data.get("body", "")
            reply = request.data.get("reply", "")
            file_ids = request.data.get("file_ids", [])
            removed_file_ids = request.data.get("removed_file_ids", [])
            DocumentRepository.remove_documents(
                [int(file_id) for file_id in removed_file_ids]
            )
            user_integration_id = request.data.get("user_integration_id", None)
            is_body_html = request.data.get("is_body_html", False)
            if not body or not reply or not user_integration_id:
                return error_response(
                    error_message="body, reply and user_integration_id are required to send reply",
                    status=400,
                )
            user_integration = IntegrationRepository.get_user_integrations(
                filters={"id": user_integration_id, "user_id": requesting_user.id},
                first=True,
                decrypt_meta_data=True,
            )
            if not user_integration:
                return error_response(
                    error_message="No user integration found, please make sure that integration hasn't been revoked.",
                    status=400,
                    logger=logger,
                    logger_message="No user integration found for given id",
                )
            service_class = integration_service_map.get(
                user_integration["integration__name"]
            )
            if service_class is None:
                raise ValueError(
                    f"Integration '{user_integration['integration__name']}' is not supported."
                )
            service_class.send_reply(
                meta_data=user_integration["meta_data"],
                user_integration=user_integration,
                body=body,
                reply=reply,
                is_body_html=is_body_html,
                file_ids=[int(file_id) for file_id in file_ids],
            )
            return success_response()
        except Exception as e:
            return error_response(
                "Error while sending reply", logger=logger, logger_message=str(e)
            )
