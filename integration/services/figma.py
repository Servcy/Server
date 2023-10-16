import requests
from django.conf import settings

from common.exceptions import ExternalIntegrationException, ServcyOauthCodeException
from integration.models import UserIntegration
from integration.repository import IntegrationRepository

from .base import BaseService

FIGMA_API_BASE_URL = "https://api.figma.com"
FIGMA_OAUTH_URL = "https://www.figma.com/api/oauth"


class FigmaService(BaseService):
    """Service class for Figma integration."""

    def __init__(self, code: str = None, refresh_token: str = None, **kwargs) -> None:
        """Initializes FigmaService."""
        self._token = None
        self._user_info = None
        if code or refresh_token:
            self.authenticate(code, refresh_token)

    def authenticate(
        self, code: str = None, refresh_token: str = None
    ) -> "FigmaService":
        """Authenticate using either code or refresh token."""
        if code:
            self._fetch_token(code)
        elif refresh_token:
            self._refresh_token(refresh_token)
        else:
            raise ServcyOauthCodeException(
                "Code/Refresh token is required for fetching access token from Figma."
            )
        self._user_info = self._fetch_user_info()
        return self

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Helper function to make requests to Figma API."""
        url = (
            f"{FIGMA_API_BASE_URL}/{endpoint}"
            if "figma.com/api" not in endpoint
            else endpoint
        )
        response = requests.request(method, url, **kwargs)
        json_response = response.json()
        if "error" in json_response:
            error_msg = f"An error occurred while communicating with Figma API.\\n{str(json_response)}"
            if json_response.get("status", 0) == 400:
                raise ExternalIntegrationException(
                    json_response.get("message", error_msg)
                )
            else:
                response.raise_for_status()
        return json_response

    def _refresh_token(self, refresh_token: str) -> None:
        """Refreshes access token from Figma."""
        data = {
            "client_id": settings.FIGMA_APP_CLIENT_ID,
            "client_secret": settings.FIGMA_APP_CLIENT_SECRET,
            "refresh_token": refresh_token,
        }
        self._token = self._make_request(
            "POST", f"{FIGMA_OAUTH_URL}/refresh", data=data
        )

    def _fetch_token(self, code: str) -> None:
        """Fetches access token from Figma."""
        data = {
            "code": code,
            "client_id": settings.FIGMA_APP_CLIENT_ID,
            "client_secret": settings.FIGMA_APP_CLIENT_SECRET,
            "redirect_uri": settings.FIGMA_APP_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        self._token = self._make_request("POST", f"{FIGMA_OAUTH_URL}/token", data=data)

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
        headers = {
            "Authorization": f"Bearer {self._token['access_token']}",
        }
        return self._make_request("GET", "v1/me", headers=headers)

    def create_webhooks(
        self, team_ids: list[str], user_integration_id: int
    ) -> list[str]:
        """Creates webhooks for Figma."""
        failed_webhooks = []
        success_webhooks = []
        success_webhook_teams = []
        for team_id in team_ids:
            data = {
                "event_type": [
                    "FILE_UPDATE",
                    "FILE_DELETE",
                    "FILE_VERSION_UPDATE",
                    "FILE_COMMENT",
                    "LIBRARY_PUBLISH",
                ],
                "team_id": team_id,
                "endpoint": f"{settings.BACKEND_URL}/webhook/figma",
                "passcode": user_integration_id,
            }
            headers = {
                "Authorization": f"Bearer {self._token['access_token']}",
            }
            try:
                webhook = self._make_request(
                    "POST", "v2/webhooks", headers=headers, json=data
                )
                success_webhooks.append(webhook["id"])
                success_webhook_teams.append(team_id)
            except ExternalIntegrationException as e:
                failed_webhooks.append(team_id)
        if failed_webhooks:
            raise ExternalIntegrationException(
                f"Failed to create webhooks for the following teams: {', '.join(failed_webhooks)}"
            )
        return success_webhooks, success_webhook_teams

    def is_active(self, meta_data, **kwargs):
        """
        Check if the user's integration is active.

        Args:
        - meta_data: The user integration meta data.

        Returns:
        - bool: True if integration is active, False otherwise.
        """
        self._refresh_token(meta_data["token"]["refresh_token"])
        IntegrationRepository.update_integraion_meta_data(
            user_integration_id=kwargs["user_integration_id"],
            meta_data={**meta_data, "token": self._token},
        )
        return True
