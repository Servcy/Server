import asana
import requests
from django.conf import settings

from common.exceptions import ServcyOauthCodeException
from integration.models import UserIntegration
from integration.repository import IntegrationRepository
from project.repository import ProjectRepository

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

    def authenticate(self, code: str) -> "AsanaService":
        """Authenticate using code."""
        self._fetch_token(code)
        self._user_info = self._fetch_user_info()
        return self

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
            raise ServcyOauthCodeException(
                f"An error occurred while obtaining access token from Asana.\n{str(token_data)}"
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
            raise ServcyOauthCodeException(
                f"An error occurred while refreshing access token from Asana.\n{str(token_data)}"
            )
        return token_data

    def _establish_webhooks(self, user_id: int) -> None:
        """Establishes webhook for Asana."""
        if not self.client:
            self.client = asana.Client.access_token(self._token["access_token"])
        for workspace in self._user_info["workspaces"]:
            self.create_project_monitoring_webhook(workspace["gid"])
            projects = self.client.projects.get_projects_for_workspace(
                workspace["gid"], opt_pretty=True
            )
            for project in projects:
                project = self.client.projects.get_project(
                    project["gid"], opt_pretty=True
                )
                ProjectRepository.create(
                    name=project["name"],
                    description=project["notes"],
                    user_id=user_id,
                    user_integration_id=self.user_integration.id,
                    uid=project["gid"],
                )
                self.create_task_monitoring_webhook(project["gid"])

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
        self._establish_webhooks(user_id)
        return self.user_integration

    def create_task_monitoring_webhook(self, project_id):
        if not self.client:
            self.client = asana.Client.access_token(self._token["access_token"])
        try:
            self.client.webhooks.create_webhook(
                resource=project_id,
                target="https://server.servcy.com/webhook/asana",
                opt_pretty=True,
                filters=[
                    {
                        "resource_type": "task",
                    },
                    {
                        "resource_type": "attachment",
                        "action": "added",
                    },
                    {
                        "resource_type": "story",
                        "resource_subtype": "comment_added",
                    },
                ],
            )
        except asana.error.ForbiddenError as err:
            if "duplicate" in str(err.message).lower():
                return
            raise err

    def create_project_monitoring_webhook(self, workspace_id):
        if not self.client:
            self.client = asana.Client.access_token(self._token["access_token"])
        try:
            self.client.webhooks.create_webhook(
                resource=workspace_id,
                target="https://server.servcy.com/webhook/asana",
                opt_pretty=True,
                filters=[
                    {
                        "resource_type": "project",
                        "action": "added",
                    },
                ],
            )
        except asana.error.ForbiddenError as err:
            if "duplicate" in str(err.message).lower():
                return
            raise err

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

    def get_project(self, project_gid: str) -> dict:
        """Get project details."""
        if not self.client:
            self.client = asana.Client.access_token(self._token["access_token"])
        project = self.client.projects.get_project(project_gid, opt_pretty=True)
        return project

    def get_task(self, task_gid: str) -> dict:
        """Get task details."""
        if not self.client:
            self.client = asana.Client.access_token(self._token["access_token"])
        task = self.client.tasks.get_task(task_gid, opt_pretty=True)
        return task
