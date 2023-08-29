import logging
import urllib.parse

from rest_framework import status, viewsets
from rest_framework.decorators import action

from common.exceptions import ServcyOauthCodeException
from common.responses import error_response, success_response
from integration.repository import IntegrationRepository
from integration.services.figma import FigmaService
from integration.services.github import GithubService
from integration.services.google import GoogleService
from integration.services.microsoft import MicrosoftService
from integration.services.notion import NotionService
from integration.services.slack import SlackService

logger = logging.getLogger(__name__)


class OauthViewset(viewsets.ViewSet):
    @action(detail=False, methods=["put"], url_path="google")
    def google(self, request):
        try:
            code = urllib.parse.unquote(request.data["code"])
            scopes = urllib.parse.unquote(request.data["scope"]).split(" ")
            if not set(scopes).issubset(set(GoogleService.scopes)):
                return error_response(
                    logger=logger,
                    logger_message="An error occurred processing oauth request.",
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                    error_message="Please grant all permissions, and try again!",
                )
            token_response = GoogleService.fetch_tokens(code)
            if "error" in token_response:
                return error_response(
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
                return error_response(
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
                account_display_name=user_info["email"],
            )
            return success_response(
                success_message="Successfully integrated with Gmail!",
                status=status.HTTP_200_OK,
            )
        except KeyError:
            return error_response(
                logger=logger,
                logger_message="KeyError occurred processing oauth request.",
                error_message="code, and scope are required!",
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="An error occurred processing oauth request.",
            )

    @action(detail=False, methods=["put"], url_path="microsoft")
    def microsoft(self, request):
        try:
            code = urllib.parse.unquote(request.data["code"])
            service = MicrosoftService(code)
            subscription = service.create_subscription(
                user_id=request.user.id,
            )
            service.create_integration(
                user_id=request.user.id, subscription=subscription
            )
            return success_response(
                success_message="Successfully integrated with Outlook!",
                status=status.HTTP_200_OK,
            )
        except ServcyOauthCodeException as error:
            return error_response(
                logger=logger,
                logger_message=error.message,
                error_message="An error occurred while integrating with Outlook. Please try again later.",
            )
        except KeyError:
            return error_response(
                logger=logger,
                logger_message="KeyError occurred processing oauth request.",
                error_message="code, and scope are required!",
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="An error occurred processing oauth request.",
            )

    @action(detail=False, methods=["put"], url_path="notion")
    def notion(self, request):
        try:
            code = urllib.parse.unquote(request.data["code"])
            service = NotionService(code)
            service.create_integration(user_id=request.user.id)
            return success_response(
                success_message="Successfully integrated with Notion!",
                status=status.HTTP_200_OK,
            )
        except ServcyOauthCodeException as error:
            return error_response(
                logger=logger,
                logger_message=error.message,
                error_message="An error occurred while integrating with Notion. Please try again later.",
            )
        except KeyError:
            return error_response(
                logger=logger,
                logger_message="KeyError occurred processing oauth request.",
                error_message="code is required!",
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="An error occurred processing oauth request.",
            )

    @action(detail=False, methods=["put"], url_path="slack")
    def slack(self, request):
        try:
            code = urllib.parse.unquote(request.data["code"])
            service = SlackService(code)
            service.create_integration(user_id=request.user.id)
            return success_response(
                success_message="Successfully integrated with Slack!",
                status=status.HTTP_200_OK,
            )
        except ServcyOauthCodeException as error:
            return error_response(
                logger=logger,
                logger_message=error.message,
                error_message="An error occurred while integrating with Slack. Please try again later.",
            )
        except KeyError:
            return error_response(
                logger=logger,
                logger_message="KeyError occurred processing oauth request.",
                error_message="code is required!",
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="An error occurred processing oauth request.",
            )

    @action(detail=False, methods=["put"], url_path="figma")
    def figma(self, request):
        try:
            code = urllib.parse.unquote(request.data["code"])
            service = FigmaService(code)
            user_integration = service.create_integration(user_id=request.user.id)
            return success_response(
                results={
                    "additionalInputsNeeded": [
                        {
                            "multiple": True,
                            "type": "text",
                            "uid": "team_id",
                            "label": "Team Id",
                            "endpoint": "integration/figma/update-teams",
                            "user_integration_id": user_integration.id,
                        }
                    ]
                },
                success_message="Successfully integrated with Figma!",
                status=status.HTTP_200_OK,
            )
        except ServcyOauthCodeException as error:
            return error_response(
                logger=logger,
                logger_message=error.message,
                error_message="An error occurred while integrating with Figma. Please try again later.",
            )
        except KeyError:
            return error_response(
                logger=logger,
                logger_message="KeyError occurred processing oauth request.",
                error_message="code is required!",
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="An error occurred processing oauth request.",
            )

    @action(detail=False, methods=["put"], url_path="github")
    def github(self, request):
        try:
            code = urllib.parse.unquote(request.data["code"])
            service = GithubService(code)
            service.create_integration(user_id=request.user.id)
            return success_response(
                success_message="Successfully integrated with Github!",
                status=status.HTTP_200_OK,
            )
        except ServcyOauthCodeException as error:
            return error_response(
                logger=logger,
                logger_message=error.message,
                error_message="An error occurred while integrating with Github. Please try again later.",
            )
        except KeyError:
            return error_response(
                logger=logger,
                logger_message="KeyError occurred processing oauth request.",
                error_message="code is required!",
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="An error occurred processing oauth request.",
            )
