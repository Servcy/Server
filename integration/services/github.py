import re

import requests
from django.conf import settings

from integration.models import UserIntegration
from integration.repository import IntegrationRepository
from project.models import Issue

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
        elif kwargs.get("token"):
            self._token = kwargs.get("token")
            self._user_info = self._fetch_user_info()

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
            response.raise_for_status()
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
            response.raise_for_status()
        self._token = token_data

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

    def authenticate(self, code: str) -> "GithubService":
        """Authenticate using code."""
        self._fetch_token(code)
        self._user_info = self._fetch_user_info()
        return self

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

    def get_possible_issue_identifiers(self, payload: dict):
        """
        If issue identifier is present in pull request title, or body then return possible issue identifiers.
        """
        pr_title = payload.get("pull_request", {}).get("title", "")
        pr_body = payload.get("pull_request", {}).get("body", "")
        comment = payload.get("comment", {}).get("body", "")
        text = f"{pr_title} {pr_body} {comment}"

        commit_map = {}
        # If commit message is present, then fetch commit message and add it to text
        commit_sha = payload.get("after", "")
        if commit_sha:
            commit_message = self._make_request(
                "GET",
                f"repos/{payload['repository']['full_name']}/git/commits/{commit_sha}",
                headers={
                    "Authorization": f"Bearer {self._token['access_token']}",
                    "Accept": "application/vnd.github+json",
                },
            ).get("message", "")
            text = f"{text} {commit_message}"
            commit_map[commit_sha] = commit_message

        return set(re.findall(r"\[([A-Z]+-\d+)\]", text)), commit_map

    def post_comment_on_pr(self, pull_request: dict, possible_issue_identifiers: set):
        """
        Post comment on PR with related issue details.
        """
        issues = []
        for identifier in possible_issue_identifiers:
            try:
                project_identifier = identifier.split("-")[0]
                sequence_id = int(identifier.split("-")[1])
                issue = Issue.objects.filter(
                    project__archived_at__isnull=True,
                    is_draft=False,
                    archived_at__isnull=True,
                    project__identifier=project_identifier,
                    sequence_id=int(sequence_id),
                ).first()
                if not issue:
                    continue
                issues.append(issue)
            except IndexError:
                continue
            except ValueError:
                continue
        comment = "**Following Servcy issues were mentioned in this PR**."
        for issue in issues:
            identifier = f"{issue.project.identifier}-{issue.sequence_id}"
            name = issue.name
            updated_at = issue.updated_at.strftime("%b %d, %Y %I:%M%p")
            state = issue.state.group
            workspace = issue.workspace
            comment += f"""

| Name | State | Preview | Updated (UTC) |
| :--- | :--- | :----- | :------ | :------- | :------ |
| **{name}** | {state} | [{identifier}]({settings.FRONTEND_URL}/{workspace.slug}/projects/{issue.project.id}/issues/{issue.id}) | {updated_at} |

"""
        self._make_request(
            "POST",
            f"repos/{pull_request['base']['repo']['full_name']}/issues/{pull_request['number']}/comments",
            json={"body": comment},
            headers={
                "Authorization": f"Bearer {self._token['access_token']}",
                "Accept": "application/vnd.github+json",
            },
        )
