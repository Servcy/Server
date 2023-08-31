import requests
from django.conf import settings

from common.exceptions import ServcyOauthCodeException
from integration.repository import IntegrationRepository

SLACK_TOKEN_URL = "https://slack.com/api/oauth.v2.access"


class SlackService:
    """Service class for Slack integration."""

    def __init__(self, code: str = None) -> None:
        """Initialize the SlackService with an optional authorization code.

        :param code: Authorization code
        """
        self._token = None
        if code:
            self._fetch_token(code)

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
        ).json()

        if "error" in response:
            raise ServcyOauthCodeException(
                f"An error occurred while obtaining access token from Slack.\\n{str(response)}"
            )
        self._token = response

    def create_integration(self, user_id: int):
        """Create a user integration in the local database with token and team details from Slack.

        :param user_id: ID of the user for whom the integration is created
        """
        return IntegrationRepository.create_user_integration(
            integration_id=IntegrationRepository.get_integration(
                filters={"name": "Slack"}
            ).id,
            user_id=user_id,
            account_id=self._token["authed_user"]["id"],
            meta_data={"token": self._token},
            account_display_name=self._token["team"]["name"],
        )
