import requests
from django.conf import settings

from common.exceptions import ServcyOauthCodeException
from integration.repository import IntegrationRepository


class GithubService:
    """
    Service class for Slack integration.
    """

    def __init__(self, code: str = None) -> None:
        """Initializes GithubService."""
        self._token = None
        if code:
            self._fetch_token(code)
        self._user_info = self._fetch_user_info()

    def _fetch_token(self, code: str) -> dict:
        """Fetches access token from Github."""
        self._token = requests.post(
            url="https://github.com/login/oauth/access_token",
            data={
                "code": code,
                "client_id": settings.GITHUB_APP_CLIENT_ID,
                "client_secret": settings.GITHUB_APP_CLIENT_SECRET,
                "redirect_uri": settings.GITHUB_APP_REDIRECT_URI,
            },
        )
        self._token = dict(
            [tuple(token.split("=")) for token in self._token.text.split("&") if token]
        )
        if "error" in self._token:
            raise ServcyOauthCodeException(
                f"An error occurred while obtaining access token from Slack.\n{str(self._token)}"
            )

    def create_integration(self, user_id: int) -> None:
        """Creates integration for user."""
        IntegrationRepository.create_user_integration(
            integration_id=IntegrationRepository.get_integration(
                filters={"name": "Github"}
            ).id,
            user_id=user_id,
            account_id=self._user_info["id"],
            meta_data={"token": self._token, "user_info": self._user_info},
        )

    def _fetch_user_info(self) -> dict:
        """Fetches user info from Github."""
        response = requests.get(
            url="https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {self._token['access_token']}",
                "Accept": "application/vnd.github+json",
            },
        ).json()
        return response
