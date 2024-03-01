import logging

import requests
from django.conf import settings
from slack_sdk import WebClient

from common.exceptions import IntegrationAccessRevokedException
from integration.repository import IntegrationRepository

from .base import BaseService

logger = logging.getLogger(__name__)

SLACK_TOKEN_URL = "https://slack.com/api/oauth.v2.access"


class SlackService(BaseService):
    """Service class for Slack integration."""

    def __init__(self, **kwargs) -> None:
        """Initialize the SlackService with an optional authorization code.

        :param code: Authorization code
        """
        self._token = None
        if kwargs.get("code"):
            self._fetch_token(kwargs.get("code"))
        elif kwargs.get("token"):
            self._token = kwargs.get("token")

    def _construct_token_request_data(self, code: str) -> dict:
        """Construct the request data for token fetching.

        :param code: Authorization code
        :return: Dictionary containing request data for token fetching
        """
        return {
            "code": code,
            "client_id": settings.SLACK_APP_CLIENT_ID,
            "client_secret": settings.SLACK_APP_CLIENT_SECRET,
            "redirect_uri": settings.SLACK_APP_REDIRECT_URI,
        }

    def _fetch_token(self, code: str) -> dict:
        """Fetch the access token from Slack using an authorization code.

        :param code: Authorization code
        :return: Dictionary containing token details
        """
        response = requests.post(
            url=SLACK_TOKEN_URL, data=self._construct_token_request_data(code)
        )
        if response.status_code != 200:
            response.raise_for_status()
        self._token = response.json()

    def _fetch_team_members(self) -> list:
        client = WebClient(self._token["authed_user"]["access_token"])
        if not client.auth_test().get("ok"):
            raise IntegrationAccessRevokedException(
                "The access token for the Slack integration is revoked."
            )
        users_list = client.users_list()
        members = users_list["members"]
        cursor = users_list["response_metadata"]["next_cursor"]
        while cursor:
            users_list = client.users_list(cursor=cursor)
            cursor = users_list["response_metadata"]["next_cursor"]
            members.append(users_list["members"])
        return members

    def create_integration(self, user_id: int):
        """Create a user integration in the local database with token and team details from Slack.

        :param user_id: ID of the user for whom the integration is created
        """
        members = self._fetch_team_members()
        return IntegrationRepository.create_user_integration(
            integration_id=IntegrationRepository.get_integration(
                filters={"name": "Slack"}
            ).id,
            user_id=user_id,
            account_id=self._token["authed_user"]["id"],
            meta_data={"token": self._token},
            account_display_name=self._token["team"]["name"],
            configuration=members,
        )

    def is_active(self, meta_data, **kwargs):
        """
        Check if the user's integration is active.

        Args:
        - meta_data: The user integration meta data.

        Returns:
        - bool: True if integration is active, False otherwise.
        """
        self._token = meta_data["token"]
        configuration = self._fetch_team_members()
        IntegrationRepository.update_integraion(
            kwargs.get("user_integration_id"), configuration=configuration
        )
        return True
