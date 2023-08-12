import logging
import traceback
import urllib.parse

import requests
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from integration.repository import IntegrationRepository
from integration.utils.google import get_google_credentials

logger = logging.getLogger(__name__)


class GoogleViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["put"], url_path="oauth")
    def oauth(self, request):
        try:
            code = urllib.parse.unquote(request.data["code"])
            scopes = urllib.parse.unquote(request.data["scope"]).split(" ")
            google_credentials = get_google_credentials()
            if not set(scopes).issubset(set(google_credentials.scopes)):
                logger.error(
                    f"Please grant all permissions, and try again!\n{str(scopes)}"
                )
                return Response(
                    {"detail": "Please grant all permissions, and try again!"},
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                )
            response = requests.post(
                google_credentials.token_uri,
                data={
                    "code": code,
                    "client_id": google_credentials.client_id,
                    "client_secret": google_credentials.client_secret,
                    "redirect_uri": google_credentials.redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            token_response = response.json()
            if "error" in token_response:
                logger.error(
                    f"An error occurred while obtaining access token from Google\n{str(token_response)}"
                )
                return Response(
                    {"detail": token_response["error_description"]},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            headers = {"Authorization": f'Bearer {token_response["access_token"]}'}
            response = requests.get(google_credentials.user_info_uri, headers=headers)
            user_info = response.json()
            if "error" in user_info:
                logger.error(
                    f"An error occurred while obtaining user info from Google\n{str(user_info)}"
                )
                return Response(
                    {"detail": user_info["error_description"]},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            meta_data = {**token_response, **user_info}
            account_id = user_info["sub"]
            integration = IntegrationRepository().get_integration_from_name("Gmail")
            IntegrationRepository().create_integration_user(
                integration_id=integration.id,
                user_id=request.user.id,
                account_id=account_id,
                meta_data=meta_data,
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
                f"An error occurred while verifying verification code\n{traceback.format_exc()}"
            )
            return Response(
                {"detail": "An error occurred. Please try again later!"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
