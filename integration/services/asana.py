import asana
import requests
from django.conf import settings

from common.exceptions import (
    ExternalIntegrationException,
    IntegrationAccessRevokedException,
)
from integration.models import UserIntegration
from integration.repository import IntegrationRepository

from .base import BaseService


class AsanaService(BaseService):
    _token_uri = "https://app.asana.com/-/oauth_token"
    _api_uri = "https://app.asana.com/api/1.0"

    """Service class for Asana integration."""

    def __init__(self, **kwargs) -> None:
        """Initializes AsanaService."""
        self._token = None
        self.user_integration = None
        self.client = None
        self._user_info = None
        if kwargs.get("code"):
            self.authenticate(kwargs.get("code"))
        elif kwargs.get("refresh_token"):
            self._token = AsanaService._refresh_tokens(kwargs.get("refresh_token"))
            self._user_info = self._fetch_user_info()

    def _fetch_token(self, code: str) -> None:
        """Fetches access token from Asana."""
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.ASANA_APP_CLIENT_ID,
            "client_secret": settings.ASANA_APP_CLIENT_SECRET,
            "redirect_uri": settings.ASANA_APP_REDIRECT_URI,
            "code": code,
        }
        response = requests.post(AsanaService._token_uri, data=data)
        token_data = response.json()
        if "error" in token_data:
            raise ExternalIntegrationException(
                f"An error occurred while obtaining access token from Asana",
                extra={"error": token_data},
            )
        self._token = token_data

    def _fetch_user_info(self) -> dict:
        """Fetches user info from Asana."""
        if not self.client:
            self.client = asana.Client.access_token(self._token["access_token"])
        user_info = self.client.users.me(opt_pretty=True)
        return user_info

    @staticmethod
    def _refresh_tokens(refresh_token) -> None:
        """Refreshes tokens."""
        response = requests.post(
            AsanaService._token_uri,
            data={
                "grant_type": "refresh_token",
                "client_id": settings.ASANA_APP_CLIENT_ID,
                "client_secret": settings.ASANA_APP_CLIENT_SECRET,
                "refresh_token": refresh_token,
            },
        )
        token_data = response.json()
        if "error" in token_data:
            raise IntegrationAccessRevokedException(
                f"An error occurred while refreshing tokens for Asana",
                extra={"error": token_data},
            )
        return token_data

    def authenticate(self, code: str) -> "AsanaService":
        """Authenticate using code."""
        self._fetch_token(code)
        self._user_info = self._fetch_user_info()
        return self

    def create_integration(self, user_id: int) -> UserIntegration:
        """Creates integration for user."""
        self.user_integration = IntegrationRepository.create_user_integration(
            integration_id=IntegrationRepository.get_integration(
                filters={"name": "Asana"}
            ).id,
            user_id=user_id,
            account_id=self._user_info["gid"],
            meta_data={"token": self._token, "user_info": self._user_info},
            account_display_name=self._user_info["name"],
        )
        return self.user_integration

    def is_active(self, meta_data: dict, **kwargs) -> bool:
        """
        Check if the user's integration is active.

        Args:
        - meta_data: The user integration meta data.

        Returns:
        - bool: True if integration is active, False otherwise.
        """
        self._token = AsanaService._refresh_tokens(meta_data["token"]["refresh_token"])
        IntegrationRepository.update_user_integraion(
            user_integration_id=kwargs["user_integration_id"],
            meta_data=IntegrationRepository.encrypt_meta_data(
                {
                    **meta_data,
                    "token": {
                        **meta_data["token"],
                        **self._token,
                    },
                }
            ),
        )
        return True

    def get_project(self, project_gid: str) -> dict:
        """Get project details."""
        if not self.client:
            self.client = asana.Client.access_token(self._token["access_token"])
        project = self.client.projects.get_project(project_gid, opt_pretty=True)
        return project

    def get_task(self, task_gid: str) -> dict:
        """Get task details."""
        try:
            if not self.client:
                self.client = asana.Client.access_token(self._token["access_token"])
            task = self.client.tasks.get_task(task_gid, opt_pretty=True)
            return task
        except asana.error.NotFoundError:
            raise ExternalIntegrationException("Asana task not found.")

    def get_user(self, user_gid: str) -> dict:
        """Get user details."""
        if not self.client:
            self.client = asana.Client.access_token(self._token["access_token"])
        user = self.client.users.get_user(user_gid, opt_pretty=True)
        return user

    def get_story(self, story_gid: str) -> dict:
        """Get story details."""
        if not self.client:
            self.client = asana.Client.access_token(self._token["access_token"])
        story = self.client.stories.get_story(story_gid, opt_pretty=True)
        return story
