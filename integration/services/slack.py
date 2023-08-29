import requests
from django.conf import settings

from common.exceptions import ServcyOauthCodeException
from integration.repository import IntegrationRepository


class SlackService:
    """
    Service class for Slack integration.
    """

    def __init__(self, code: str = None) -> None:
        """Initializes SlackService."""
        self._token = None
        if code:
            self._fetch_token(code)

    def _fetch_token(self, code: str) -> dict:
        """Fetches access token from Slack."""
        self._token = requests.post(
            url="https://slack.com/api/oauth.v2.access",
            data={
                "code": code,
                "client_id": settings.SLACK_APP_CLIENT_ID,
                "client_secret": settings.SLACK_APP_CLIENT_SECRET,
                "redirect_uri": settings.SLACK_APP_REDIRECT_URI,
            },
        ).json()
        if "error" in self._token:
            raise ServcyOauthCodeException(
                f"An error occurred while obtaining access token from Slack.\n{str(self._token)}"
            )

    def create_integration(self, user_id: int) -> None:
        """Creates integration for user."""
        IntegrationRepository.create_user_integration(
            integration_id=IntegrationRepository.get_integration(
                filters={"name": "Slack"}
            ).id,
            user_id=user_id,
            account_id=self._token["authed_user"]["id"],
            meta_data={"token": self._token},
            account_display_name=self._token["team"]["name"],
        )
