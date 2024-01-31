import requests
import json
from django.conf import settings

from common.exceptions import ServcyOauthCodeException
from integration.models import UserIntegration
from integration.repository import IntegrationRepository

from .base import BaseService

GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_OAUTH_URL = "https://github.com/login/oauth"


class GithubService(BaseService):
    """Service class for Github integration."""

    def __init__(self, **kwargs) -> None:
        """Initializes GithubService."""
        self._token = None
        self._user_info = None
        if kwargs.get("code"):
            self.authenticate(kwargs.get("code"))

    def authenticate(self, code: str) -> "GithubService":
        """Authenticate using code."""
        self._fetch_token(code)
        self._user_info = self._fetch_user_info()
        return self

    @staticmethod
    def _make_request(method: str, endpoint: str, **kwargs) -> dict:
        """Helper function to make requests to Github API."""
        url = (
            f"{GITHUB_API_BASE_URL}/{endpoint}"
            if "github.com" not in endpoint
            else endpoint
        )
        response = requests.request(method, url, **kwargs)
        json_response = response.json()
        if "error" in json_response:
            error_msg = f"An error occurred while communicating with Github API.\n{str(json_response)}"
            raise ServcyOauthCodeException(error_msg)
        return json_response

    def _fetch_token(self, code: str) -> None:
        """Fetches access token from Github."""
        data = {
            "code": code,
            "client_id": settings.GITHUB_APP_CLIENT_ID,
            "client_secret": settings.GITHUB_APP_CLIENT_SECRET,
            "redirect_uri": settings.GITHUB_APP_REDIRECT_URI,
        }
        response = requests.post(f"{GITHUB_OAUTH_URL}/access_token", data=data)
        token_data = dict(
            [tuple(token.split("=")) for token in response.text.split("&") if token]
        )
        if "error" in token_data:
            raise ServcyOauthCodeException(
                f"An error occurred while obtaining access token from Github.\n{str(token_data)}"
            )
        self._token = token_data

    def create_integration(self, user_id: int) -> UserIntegration:
        """Creates integration for user."""
        return IntegrationRepository.create_user_integration(
            integration_id=IntegrationRepository.get_integration(
                filters={"name": "Github"}
            ).id,
            user_id=user_id,
            account_id=self._user_info["id"],
            meta_data={"token": self._token, "user_info": self._user_info},
            account_display_name=self._user_info["login"],
        )

    def _fetch_user_info(self) -> dict:
        """Fetches user info from Github."""
        return GithubService._make_request(
            "GET",
            "user",
            headers={
                "Authorization": f"Bearer {self._token['access_token']}",
                "Accept": "application/vnd.github+json",
            },
        )

    def is_active(self, meta_data, **kwargs):
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

    @staticmethod
    def manage_github_repositories(payload: dict) -> None:
        """
        Used for installation event especially created and deleted action
        """
        action = payload["action"]
        account_id = payload["sender"]["id"]
        user_integration = IntegrationRepository.get_user_integration(
            {"integration__name": "Github", "account_id": account_id}
        )
        installation_ids = set(user_integration.configuration or [])
        if action == "created":
            installation_ids.add(str(payload["installation"]["id"]))
        elif (
            action == "deleted"
            and str(payload["installation"]["id"]) in installation_ids
        ):
            installation_ids.remove(str(payload["installation"]["id"]))
        elif action == "added":
            for repo in payload["repositories_added"]:
                installation_ids.add(str(repo["id"]))
        elif action == "removed":
            for repo in payload["repositories_removed"]:
                if str(repo["id"]) in installation_ids:
                    installation_ids.remove(str(repo["id"]))
        user_integration.configuration = list(installation_ids)
        user_integration.save()

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

    @staticmethod
    def send_reply(
        meta_data: dict,
        body: str,
        reply: str,
        **kwargs,
    ):
        """
        Send reply to github.

        Args:
        - meta_data: The user integration meta data.
        - body: The event body.
        - reply: The reply to send.
        """
        user_info = meta_data["user_info"]
        tokens = meta_data["token"]
        body = json.loads(body)
        event = body["event"]
        if event == "issue_comment":
            GithubService._make_request(
                "POST",
                f"repos/{user_info['login']}/{body['repository']['name']}/issues/{body['issue']['number']}/comments",
                headers={
                    "Authorization": f"Bearer {tokens['access_token']}",
                    "Accept": "application/vnd.github+json",
                },
                json={"body": reply},
            )
        elif event == "pull_request_review_comment":
            GithubService._make_request(
                "POST",
                f"repos/{user_info['login']}/{body['repository']['name']}/pulls/{body['pull_request']['number']}/comments/{body['comment']['id']}/replies",
                headers={
                    "Authorization": f"Bearer {tokens['access_token']}",
                    "Accept": "application/vnd.github+json",
                },
                json={"body": reply},
            )
