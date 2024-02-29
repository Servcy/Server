import datetime
import logging

import msal
import requests
from django.conf import settings

from common.exceptions import ExternalIntegrationException
from common.utils.datetime import future_date_in_iso_formate
from integration.repository import IntegrationRepository

logger = logging.getLogger(__name__)

MICROSOFT_CLIENT_ID = settings.MICROSOFT_APP_CLIENT_ID
MICROSOFT_CLIENT_SECRET = settings.MICROSOFT_APP_CLIENT_SECRET
MICROSOFT_SCOPES = settings.MICROSOFT_OAUTH2_SCOPES
MICROSOFT_REDIRECT_URI = settings.MICROSOFT_APP_REDIRECT_URI
MICROSOFT_READ_MAIL_URI = "https://graph.microsoft.com/v1.0/me/messages/"
MICROSOFT_SUBSCRIPTION_URI = "https://graph.microsoft.com/v1.0/subscriptions/"
MICROSOFT_AUTHORITY_URI = "https://login.microsoftonline.com/common"


class MicrosoftService:
    """Service class for Microsoft integration."""

    def __init__(self, code: str = None, refresh_token: str = None, **kwargs) -> None:
        """Initialize the MicrosoftService with either an authorization code or refresh token.

        :param code: Authorization code
        :param refresh_token: Refresh token
        :param scopes: List of scopes for token fetching
        """
        self._scopes = settings.MICROSOFT_OAUTH2_SCOPES
        self._app = msal.ConfidentialClientApplication(
            client_id=MICROSOFT_CLIENT_ID,
            client_credential=MICROSOFT_CLIENT_SECRET,
            authority=MICROSOFT_AUTHORITY_URI,
        )
        if code:
            self._token = self._fetch_token(code)
            self._subscription = self.create_subscription()
        elif refresh_token:
            self._token = self._refresh_token(
                refresh_token=refresh_token,
            )

    def _make_microsoft_request(self, method, url, **kwargs):
        """Helper function to make requests to Microsoft API."""
        response = method(url, **kwargs).json()
        if "error" in response:
            raise ExternalIntegrationException(
                "An error occurred while making request to Microsoft",
                extra={
                    "error": response.get("error"),
                    "error_description": response.get("error_description"),
                },
            )
        return response

    def _fetch_token(
        self,
        code: str,
    ) -> None:
        """
        Exchange code for access token and refresh token.
        """
        response = self._app.acquire_token_by_authorization_code(
            code=code,
            scopes=["User.Read", "Mail.Read"],
            redirect_uri=MICROSOFT_REDIRECT_URI,
        )
        if "error" in response:
            raise ExternalIntegrationException(
                "An error occurred while obtaining access token from Microsoft",
                extra={
                    "error": response.get("error"),
                    "error_description": response.get("error_description"),
                },
            )
        return response

    def _refresh_token(self, refresh_token: str) -> dict:
        """
        Function to get new token using refresh token
        """
        return self._app.acquire_token_by_refresh_token(
            refresh_token=refresh_token,
            scopes=self._scopes,
        )

    def create_integration(self, user_id: int):
        """
        Create integration for user.
        """
        integration = IntegrationRepository.get_integration(filters={"name": "Outlook"})
        email = self._token["id_token_claims"]["email"]
        return IntegrationRepository.create_user_integration(
            integration_id=integration.id,
            user_id=user_id,
            account_id=email,
            meta_data={"token": self._token, "subscription": self._subscription},
            account_display_name=email,
        )

    def is_active(self, meta_data, **kwargs):
        """
        Check if the user's integration is active.

        Args:
        - meta_data: The user integration meta data.

        Returns:
        - bool: True if integration is active, False otherwise.
        """
        self._token = self._refresh_token(
            meta_data["token"]["refresh_token"],
        )
        subscription = meta_data["subscription"]
        expiration_date_time = datetime.datetime.strptime(
            subscription["expirationDateTime"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        if (expiration_date_time - datetime.datetime.now()).total_seconds() < 86400:
            self.renew_subscription(subscription["id"])

    def get_message(self, message_id: str) -> dict:
        """
        Function to fetch mail from outlook with ID
        """
        return self._make_microsoft_request(
            requests.get,
            f"{MICROSOFT_READ_MAIL_URI}/{message_id}",
            headers={
                "Authorization": "Bearer {}".format(self._token["access_token"]),
            },
        )

    def get_attachments(self, message_id: str) -> dict:
        """
        Function to fetch attachments from outlook with ID
        """
        return self._make_microsoft_request(
            requests.get,
            f"{MICROSOFT_READ_MAIL_URI}/{message_id}/attachments",
            headers={
                "Authorization": "Bearer {}".format(self._token["access_token"]),
            },
        )

    def create_subscription(self) -> str:
        """
        Create subscription for user to receive notifications for new emails.
        :return: subscription id
        """
        response = self._make_microsoft_request(
            requests.post,
            MICROSOFT_SUBSCRIPTION_URI,
            headers={
                "Authorization": f"Bearer {self._token['access_token']}",
                "Content-Type": "application/json",
            },
            json={
                "changeType": "created",
                "notificationUrl": f"{settings.BACKEND_URL}/webhook/microsoft",
                "resource": "me/mailFolders('Inbox')/messages?$filter=isRead eq false",
                "expirationDateTime": future_date_in_iso_formate(3, True),
                "clientState": settings.MICROSOFT_APP_CLIENT_SECRET,
            },
        )
        return response

    def renew_subscription(self, subscription_id: str) -> None:
        """
        Update subscription expiration date
        """
        self._make_microsoft_request(
            requests.patch,
            f"{MICROSOFT_SUBSCRIPTION_URI}/{subscription_id}",
            headers={
                "Authorization": f"Bearer {self._token['access_token']}",
                "Content-Type": "application/json",
            },
            json={
                "expirationDateTime": future_date_in_iso_formate(3, True),
            },
        )

    def remove_subscription(self, subscription_id: str) -> None:
        """
        Remove subscription for user.
        """
        return self._make_microsoft_request(
            requests.delete,
            f"{MICROSOFT_SUBSCRIPTION_URI}/{subscription_id}",
            headers={
                "Authorization": f"Bearer {self._token['access_token']}",
                "Content-Type": "application/json",
            },
        )
