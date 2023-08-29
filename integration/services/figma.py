import requests
from django.conf import settings

from common.exceptions import ServcyOauthCodeException
from integration.models import UserIntegration
from integration.repository import IntegrationRepository


class FigmaService:
    """
    Service class for Slack integration.
    """

    def __init__(self, code: str = None, refresh_token: str = None) -> None:
        """Initializes FigmaService."""
        self._token = None
        if code:
            self._fetch_token(code)
        elif refresh_token:
            self._refresh_token(refresh_token)
        else:
            raise ServcyOauthCodeException(
                "Code/Refresh is required for fetching access token from Figma."
            )
        self._user_info = self._fetch_user_info()

    def _refresh_token(self, refresh_token: str) -> dict:
        """
        Refreshes access token from Figma.
        """
        response = requests.post(
            url="https://www.figma.com/api/oauth/refresh",
            data={
                "client_id": settings.FIGMA_APP_CLIENT_ID,
                "client_secret": settings.FIGMA_APP_CLIENT_SECRET,
                "refresh_token": refresh_token,
            },
        ).json()
        if "error" in response:
            raise ServcyOauthCodeException(
                f"An error occurred while obtaining access token from Figma.\n{str(response)}"
            )
        return response

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

    def create_integration(self, user_id: int) -> UserIntegration:
        """Creates integration for user."""
        user_integration = IntegrationRepository.create_user_integration(
            integration_id=IntegrationRepository.get_integration(
                filters={"name": "Figma"}
            ).id,
            user_id=user_id,
            account_id=str(self._token["user_id"]),
            meta_data={"token": self._token, "user_info": self._user_info},
            account_display_name=self._user_info["email"],
        )
        return user_integration

    def _fetch_user_info(self) -> dict:
        """Fetches user info from Figma."""
        response = requests.get(
            url="https://api.figma.com/v1/me",
            headers={
                "Authorization": f"Bearer {self._token['access_token']}",
            },
        ).json()
        return response

    def create_webhooks(self, team_ids: list[str]) -> None:
        """
        Creates webhooks for Figma.
        """
        responses = []
        for team_id in team_ids:
            response = requests.post(
                url="https://api.figma.com/v2/webhooks",
                headers={
                    "Authorization": f"Bearer {self._token['access_token']}",
                },
                json={
                    "method": "POST",
                    "path": f"/v1/webhooks",
                    "body": {
                        "event_type": [
                            "FILE_UPDATE",
                            "FILE_DELETE",
                            "FILE_VERSION_UPDATE",
                            "FILE_COMMENT",
                            "LIBRARY_PUBLISH",
                        ],
                        "team_id": team_id,
                        "endpoint": f"{settings.BACKEND_URL}/webhook/figma",
                    },
                },
            )
            responses.append(response)
        return responses
