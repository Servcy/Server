import base64
import json

import requests
from django.conf import settings

from common.exceptions import ServcyOauthCodeException
from integration.repository import IntegrationRepository

NOTION_API_BASE_URL = "https://api.notion.com"
NOTION_OAUTH_TOKEN_ENDPOINT = f"{NOTION_API_BASE_URL}/v1/oauth/token"


class NotionService:
    """Service class for Notion integration."""

    def __init__(self, **kwargs) -> None:
        """Initialize the NotionService with an optional authorization code.

        :param code: Authorization code
        """
        self._token = None
        self._fetch_token(kwargs.get("code"))

    def _create_basic_auth_header(self) -> dict:
        """Generate the Basic Authorization header for Notion API requests."""
        authorization = (
            f"{settings.NOTION_APP_CLIENT_ID}:{settings.NOTION_APP_CLIENT_SECRET}"
        ).encode()
        return {
            "Accept": "application/json",
            "Authorization": f"Basic {base64.b64encode(authorization).decode()}",
        }

    def _fetch_token(self, code: str) -> dict:
        """Fetch the access token from Notion using an authorization code.

        :param code: Authorization code
        :return: Dictionary containing token details
        """
        response = requests.post(
            url=NOTION_OAUTH_TOKEN_ENDPOINT,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.NOTION_APP_REDIRECT_URI,
            },
            headers=self._create_basic_auth_header(),
        ).json()

        if response.get("object") == "error" or "error" in response:
            raise ServcyOauthCodeException(
                f"An error occurred while obtaining access token from Notion.\n{str(response)}"
            )
        self._token = response

    def create_integration(self, user_id: int):
        """Create a user integration in the local database with token and workspace details.

        :param user_id: ID of the user for whom the integration is created
        """
        return IntegrationRepository.create_user_integration(
            integration_id=IntegrationRepository.get_integration(
                filters={"name": "Notion"}
            ).id,
            user_id=user_id,
            account_id=self._token["workspace_id"],
            account_display_name=self._token["workspace_name"],
            meta_data={"token": self._token},
        )

    def is_active(self, meta_data):
        """
        Check if the user's integration is active.

        Args:
        - meta_data: The user integration meta data.

        Returns:
        - bool: True if integration is active, False otherwise.
        """
        token = meta_data.get("token")
        token = json.loads(token.replace("'", '"')) if isinstance(token, str) else token
        self._token = token
        response = requests.get(
            url=f"{NOTION_API_BASE_URL}/v1/users",
            headers={
                "Authorization": f"Bearer {self._token['access_token']}",
                "Notion-Version": "2021-05-13",
            },
        )
        return response.status_code == 200
