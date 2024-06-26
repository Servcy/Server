import logging
import urllib.parse

from rest_framework import status
from rest_framework.decorators import action

from common.responses import error_response, success_response
from common.views import BaseViewSet
from integration.services.asana import AsanaService
from integration.services.figma import FigmaService
from integration.services.github import GithubService
from integration.services.google import GOOGLE_SCOPES, GoogleService
from integration.services.jira import JiraService
from integration.services.microsoft import MicrosoftService
from integration.services.notion import NotionService
from integration.services.slack import SlackService
from integration.services.trello import TrelloService

logger = logging.getLogger(__name__)


class OauthViewset(BaseViewSet):
    def _handle_oauth_code(self, request, service_class, service_name: str):
        """Generalized method to handle OAuth2 authorization flow for a given service.

        :param request: The HTTP request object.
        :param service_class: The service class responsible for the OAuth2 flow.
        :param service_name: The name of the service for logging and error messages.
        :return: HTTP response.
        """
        try:
            code = urllib.parse.unquote(request.data["code"])
            service = service_class(code=code, user_id=request.user.id)
            user_integration = service.create_integration(user_id=request.user.id)
            return success_response(
                results=(
                    {"redirect_uri": f"{user_integration.integration.configure_at}"}
                    if user_integration.integration.configure_at is not None
                    else None
                ),
                success_message=f"Successfully integrated with {service_name}!",
                status=status.HTTP_200_OK,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="An unexpected error occurred processing oauth request.",
            )

    @action(detail=False, methods=["put"], url_path="gmail")
    def gmail(self, request):
        """Handle OAuth2 authorization flow for Google."""
        scopes = urllib.parse.unquote(request.data.get("scope", "")).split(" ")
        if not set(scopes).issubset(set(GOOGLE_SCOPES)):
            return error_response(
                logger=logger,
                logger_message=f"User did not grant all permissions for Google.",
                status=status.HTTP_406_NOT_ACCEPTABLE,
                error_message="Please grant all permissions, and try again!",
            )
        return self._handle_oauth_code(request, GoogleService, "Google")

    @action(detail=False, methods=["put"], url_path="outlook")
    def outlook(self, request):
        """Handle OAuth2 authorization flow for Microsoft."""
        return self._handle_oauth_code(request, MicrosoftService, "Microsoft")

    @action(detail=False, methods=["put"], url_path="notion")
    def notion(self, request):
        return self._handle_oauth_code(request, NotionService, "Notion")

    @action(detail=False, methods=["put"], url_path="slack")
    def slack(self, request):
        return self._handle_oauth_code(request, SlackService, "Slack")

    @action(detail=False, methods=["put"], url_path="figma")
    def figma(self, request):
        return self._handle_oauth_code(request, FigmaService, "Figma")

    @action(detail=False, methods=["put"], url_path="github")
    def github(self, request):
        return self._handle_oauth_code(request, GithubService, "Github")

    @action(detail=False, methods=["put"], url_path="asana")
    def asana(self, request):
        return self._handle_oauth_code(request, AsanaService, "Asana")

    @action(detail=False, methods=["put"], url_path="trello")
    def trello(self, request):
        return self._handle_oauth_code(request, TrelloService, "Trello")

    @action(detail=False, methods=["put"], url_path="jira")
    def jira(self, request):
        return self._handle_oauth_code(request, JiraService, "Atlassian")
