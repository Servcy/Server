import requests
from django.conf import settings

from integration.models import UserIntegration
from integration.repository import IntegrationRepository

from .base import BaseService


class TrelloService(BaseService):
    """
    Service class for Trello integration.
    """

    _token_uri = "https://trello.com/1/OAuthGetAccessToken"
    _trello_secret = settings.TRELLO_APP_CLIENT_SECRET
    _trello_redirect_uri = settings.TRELLO_APP_REDIRECT_URI
    _trello_key = settings.TRELLO_APP_KEY

    def __init__(self, **kwargs) -> None:
        """
        Initializes TrelloService.
        """
        self._token = kwargs.get("code")
        self._user_info = self._fetch_user_info() if self._token else {}
        self.user_integration = None

    def _fetch_user_info(self) -> dict:
        """
        Fetches user info from Trello.
        """
        response = requests.get(
            f"https://api.trello.com/1/members/me?key={self._trello_key}&token={self._token}"
        )
        if response.status_code != 200:
            response.raise_for_status()
        return response.json()

    def _fetch_token(self, code: str):
        """Abstract method implementation"""
        return super()._fetch_token(code)

    def create_integration(self, user_id: int) -> UserIntegration:
        """Creates integration for user."""
        self.user_integration = IntegrationRepository.create_user_integration(
            integration_id=IntegrationRepository.get_integration(
                filters={"name": "Trello"}
            ).id,
            user_id=user_id,
            account_id=self._user_info["id"],
            meta_data={"token": self._token, "user_info": self._user_info},
            account_display_name=self._user_info["username"],
        )
        # https://developer.atlassian.com/cloud/trello/guides/rest-api/webhooks/#webhook-actions-and-types
        return self.user_integration

    def is_active(self, meta_data: dict, **kwargs) -> bool:
        """
        Check if the user's integration is active.

        Args:
        - meta_data: The user integration meta data.

        Returns:
        - bool: True if integration is active, False otherwise.
        """
        self._token = meta_data["token"]
        self._fetch_user_info()
        return True
