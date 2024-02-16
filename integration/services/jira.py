import logging
import traceback
import requests
from django.conf import settings

from common.exceptions import ServcyOauthCodeException
from integration.models import UserIntegration
from integration.repository import IntegrationRepository

from .base import BaseService

logger = logging.getLogger(__name__)


class JiraService(BaseService):
    _jira_redirect_uri = settings.JIRA_APP_REDIRECT_URI
    _jira_client_id = settings.JIRA_APP_CLIENT_ID
    _jira_app_id = settings.JIRA_APP_ID
    _jira_app_secret = settings.JIRA_APP_CLIENT_SECRET
    _jira_api_url = "https://api.atlassian.com"
    _jira_auth_url = "https://auth.atlassian.com"

    def __init__(self, **kwargs) -> None:
        self._token = (
            self._fetch_token(kwargs.get("code"))
            if kwargs.get("code")
            else kwargs.get("token")
        )
        self.user_integration = None
        self.cloud_id = None
        self._fetch_cloud_id()
        self._user_info = self._fetch_user_info()

    def _fetch_token(self, code: str):
        """
        Fetches token from Jira.
        """
        data = {
            "grant_type": "authorization_code",
            "client_id": self._jira_client_id,
            "client_secret": self._jira_app_secret,
            "code": code,
            "redirect_uri": self._jira_redirect_uri,
        }
        token_info = requests.post(f"{self._jira_auth_url}/oauth/token", data=data)
        if token_info.status_code != 200:
            raise ServcyOauthCodeException(
                f"An error occurred while obtaining token from Jira.\n{str(token_info.json())}"
            )
        return token_info.json()

    def _fetch_cloud_id(self):
        """
        Fetches cloud ids for Jira and Confluence.
        """
        response = requests.get(
            f"{self._jira_api_url}/oauth/token/accessible-resources",
            headers={
                "Authorization": f"Bearer {self._token['access_token']}",
                "Accept": "application/json",
            },
        )
        if response.status_code != 200:
            raise ServcyOauthCodeException(
                f"An error occurred while obtaining cloud ids from Jira.\n{str(response)}"
            )
        self.cloud_id = response.json()[0]["id"]

    def _fetch_user_info(self) -> dict:
        """
        Fetches user info from Jira.
        """
        user_info = requests.get(
            f"{self._jira_api_url}/me",
            headers={"Authorization": f"Bearer {self._token['access_token']}"},
        )
        if user_info.status_code != 200:
            raise ServcyOauthCodeException(
                f"An error occurred while obtaining user info from Jira.\n{str(user_info.json())}"
            )
        return user_info.json()

    def is_active(self, meta_data: dict, **kwargs) -> bool:
        """
        Checks if integration is active.
        """
        self._token = meta_data["token"]
        self._fetch_user_info()
        return True

    def create_integration(self, user_id: int) -> UserIntegration:
        """
        Create integration for user.
        """
        self.user_integration = IntegrationRepository.create_user_integration(
            integration_id=IntegrationRepository.get_integration(
                filters={"name": "Jira"}
            ).id,
            user_id=user_id,
            meta_data={
                "token": self._token,
                "user_info": self._user_info,
                "cloud_id": self.cloud_id,
            },
            account_id=self._user_info["account_id"],
            account_display_name=self._user_info["email"],
        )
        self.create_webhook()
        return self.user_integration

    def fetch_webhooks(self) -> list:
        """
        Fetch webhooks for Jira integration.
        """
        response = requests.get(
            f"{self._jira_api_url}/ex/jira/{self.cloud_id}/rest/api/3/webhook",
            headers={
                "Authorization": f"Bearer {self._token['access_token']}",
                "Accept": "application/json",
            },
        )
        if response.status_code != 200:
            raise ServcyOauthCodeException(
                f"An error occurred while fetching webhooks for Jira.\n{str(response.json())}"
            )
        return response.json().get("values", [])

    def create_webhook(self) -> None:
        """
        Create webhooks for Jira integration.
        """
        existing_webhooks = self.fetch_webhooks()
        for webhook in existing_webhooks:
            if webhook["url"] == f"{settings.BACKEND_URL}/webhook/jira":
                return
        response = requests.post(
            f"{self._jira_api_url}/ex/jira/{self.cloud_id}/rest/api/3/webhook",
            headers={
                "Authorization": f"Bearer {self._token['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json={
                "url": f"{settings.BACKEND_URL}/webhook/jira",
                "webhooks": [
                    {
                        "events": [
                            "jira:issue_created",
                            "jira:issue_updated",
                            "jira:issue_deleted",
                        ],
                        "jqFilter": f"assignee = {self._user_info['account_id']}",
                    },
                    {
                        "events": [
                            "comment_created",
                            "comment_updated",
                            "comment_deleted",
                        ],
                    },
                ],
            },
        )
        if response.status_code != 200:
            raise ServcyOauthCodeException(
                f"An error occurred while creating webhooks for Jira.\n{str(response.json())}"
            )

    def extend_webhook(self) -> None:
        """
        Extend webhook for Jira integration.
        """
        webhooks = self.fetch_webhooks()
        webhook_ids = [webhook["id"] for webhook in webhooks]
        response = requests.put(
            f"{self._jira_api_url}/ex/jira/{self.cloud_id}/rest/api/3/webhook/refresh",
            headers={
                "Authorization": f"Bearer {self._token['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json={
                "webhookId": webhook_ids,
            },
        )
        if response.status_code != 200:
            logger.exception(
                f"An error occurred while extending webhooks for Jira.\n{str(response.json())}",
                extra={
                    "traceback": traceback.format_exc(),
                },
            )

    def refresh_token(self):
        """
        Refreshes token for Jira integration.
        """
        data = {
            "grant_type": "refresh_token",
            "client_id": self._jira_client_id,
            "client_secret": self._jira_app_secret,
            "refresh_token": self._token["refresh_token"],
        }
        token_info = requests.post(f"{self._jira_auth_url}/oauth/token", data=data)
        if token_info.status_code != 200:
            raise ServcyOauthCodeException(
                f"An error occurred while refreshing token for Jira.\n{str(token_info.json())}"
            )
        return token_info.json()


def refresh_jira_webhooks_and_tokens():
    """
    Refreshes Jira webhooks and tokens.
    """

    try:
        user_integrations = IntegrationRepository.get_user_integrations(
            {
                "integration__name": "Jira",
            }
        )
        for user_integration in user_integrations:
            try:
                jira_service = JiraService(
                    token=user_integration["meta_data"]["token"],
                    cloud_id=user_integration["meta_data"]["cloud_id"],
                )
                jira_service.extend_webhook()
                new_tokens = jira_service.refresh_token()
                IntegrationRepository.update_integraion_meta_data(
                    user_integration_id=user_integration["id"],
                    meta_data={
                        **user_integration["meta_data"],
                        "token": {
                            **user_integration["meta_data"]["token"],
                            **new_tokens,
                        },
                    },
                )
            except:
                logger.exception(
                    f"Error in refreshing webhooks and tokens for Jira",
                    extra={
                        "traceback": traceback.format_exc(),
                    },
                )
                continue
    except Exception:
        logger.exception(
            f"Error in refreshing webhooks and tokens for Jira",
            extra={
                "traceback": traceback.format_exc(),
            },
        )
