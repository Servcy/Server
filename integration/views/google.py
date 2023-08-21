import logging
import urllib.parse

from rest_framework import status, viewsets
from rest_framework.decorators import action

from common.responses import error_response, success_response
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
                error_response(
                    logger=logger,
                    logger_message="An error occurred processing oauth request.",
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                    error_message="Please grant all permissions, and try again!",
                )
            token_response = GoogleService.fetch_tokens(code)
            if "error" in token_response:
                error_response(
                    logger=logger,
                    logger_message=f"An error occurred while obtaining access token from Google.\n{str(token_response)}",
                    error_message=token_response["error_description"],
                )
            google_service = GoogleService(
                token=token_response["access_token"],
                refresh_token=token_response["refresh_token"],
            )
            user_info = google_service.fetch_user_info()
            if "error" in user_info:
                error_response(
                    logger=logger,
                    logger_message=f"An error occurred while obtaining user info from Google.\n{str(user_info)}",
                    error_message=user_info["error_description"],
                )
            google_service.add_publisher_for_user(
                email=user_info["email"],
            )
            watcher_response = google_service.add_watcher_to_inbox_pub_sub(
                user_info["email"]
            )
            integration = IntegrationRepository.get_integration(
                filters={"name": "Gmail"}
            )
            IntegrationRepository.create_user_integration(
                integration_id=integration.id,
                user_id=request.user.id,
                account_id=user_info["email"],
                meta_data={**token_response, **user_info, **watcher_response},
            )
            return success_response(
                success_message="Successfully integrated with Gmail!",
                status=status.HTTP_200_OK,
            )
        except KeyError:
            error_response(
                logger=logger,
                logger_message="KeyError occurred processing oauth request.",
                error_message="code, and scope are required!",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            error_response(
                logger=logger,
                logger_message="An error occurred processing oauth request.",
            )
