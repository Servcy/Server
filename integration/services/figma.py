import requests
from django.conf import settings

from common.exceptions import ServcyOauthCodeException
from integration.repository import IntegrationRepository


class FigmaService:
    """
    Service class for Slack integration.
    """

    def __init__(self, code: str = None) -> None:
        """Initializes FigmaService."""
        self._token = None
        if code:
            self._fetch_token(code)

    def _fetch_token(self, code: str) -> dict:
        """Fetches access token from Notion."""
        self._token = requests.post(
            url="https://www.figma.com/api/oauth/token",
            data={
                "code": code,
                "client_id": settings.FIGMA_APP_CLIENT_ID,
                "client_secret": settings.FIGMA_APP_CLIENT_SECRET,
                "redirect_uri": settings.FIGMA_APP_REDIRECT_URI,
                "grant_type": "authorization_code",
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
                filters={"name": "Figma"}
            ).id,
            user_id=user_id,
            account_id=str(self._token["user_id"]),
            meta_data={"token": self._token, "user_info": self._user_info},
        )
