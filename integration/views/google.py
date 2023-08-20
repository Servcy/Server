import logging
import traceback
import urllib.parse

import requests
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from integration.repository import IntegrationRepository
from integration.services.google import GoogleService

logger = logging.getLogger(__name__)


class GoogleViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["put"], url_path="oauth")
    def oauth(self, request):
        try:
            code = urllib.parse.unquote(request.data["code"])
            scopes = urllib.parse.unquote(request.data["scope"]).split(" ")
            if not set(scopes).issubset(set(GoogleService.scopes)):
                logger.error(
                    f"Please grant all permissions, and try again!\n{str(scopes)}"
                )
                return Response(
                    {"detail": "Please grant all permissions, and try again!"},
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                )
            token_response = GoogleService.fetch_tokens(code)
            if "error" in token_response:
                logger.error(
                    f"An error occurred while obtaining access token from Google.\n{str(token_response)}"
                )
                return Response(
                    {"detail": token_response["error_description"]},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            google_service = GoogleService(
                token=token_response["access_token"],
                refresh_token=token_response["refresh_token"],
            )
            user_info = google_service.fetch_user_info()
            if "error" in user_info:
                logger.error(
                    f"An error occurred while obtaining user info from Google.\n{str(user_info)}"
                )
                return Response(
                    {"detail": user_info["error_description"]},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            google_service.add_publisher_for_user(
                email=user_info["email"],
            )
            watcher_response = google_service.add_watcher_to_inbox_pub_sub(
                access_token=token_response["access_token"],
                refresh_token=token_response["refresh_token"],
                email=user_info["email"],
            )
            integration = IntegrationRepository.get_integration(
                filters={"name": "Gmail"}
            )
            IntegrationRepository.create_integration_user(
                integration_id=integration.id,
                user_id=request.user.id,
                account_id=user_info["email"],
                meta_data={**token_response, **user_info, **watcher_response},
            )
            return Response(
                {"detail": "Successfully integrated with Gmail!"},
                status=status.HTTP_200_OK,
            )
        except KeyError:
            logger.error(f"Code, and scope are required!\n{traceback.format_exc()}")
            return Response(
                {"detail": "code, and scope are required! Please try again later!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            logger.error(
                f"An error occurred while processing oauth data.\n{traceback.format_exc()}"
            )
            return Response(
                {"detail": "An error occurred. Please try again later!"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
