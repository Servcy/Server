import logging

import msal
import requests
from django.conf import settings

from common.exceptions import ServcyOauthCodeException
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

    def __init__(
        self, code: str = None, refresh_token: str = None, scopes: list = None, **kwargs
    ) -> None:
        """Initialize the MicrosoftService with either an authorization code or refresh token.

        :param code: Authorization code
        :param refresh_token: Refresh token
        :param scopes: List of scopes for token fetching
        """
        if scopes is None:
            scopes = ["User.Read", "Mail.Read"]
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
                scopes=scopes,
            )

    def _make_microsoft_request(self, method, url, **kwargs):
        """Helper function to make requests to Microsoft API."""
        response = method(url, **kwargs).json()
        if "error" in response:
            if response["error"]["code"] == "InvalidAuthenticationToken":
                self._token = self._refresh_token(
                    refresh_token=self._token["refresh_token"],
                    scopes=["User.Read", "Mail.Read"],
                )
                return self._make_microsoft_request(method, url, **kwargs)
            else:
                logger.exception(
                    f"Error in making request to Microsoft API: {response['error']['message']}"
                )
                raise Exception(response["error"]["message"])
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
            raise ServcyOauthCodeException(
                f"An error occurred while obtaining access token from Microsoft.\n{str(response)}"
            )
        return response

    def _refresh_token(
        self, refresh_token: str, scopes: list = ["User.Read", "Mail.Read"]
    ) -> dict:
        """
        Function to get new token using refresh token
        """
        return self._app.acquire_token_by_refresh_token(
            refresh_token=refresh_token,
            scopes=scopes,
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
                "clientState": self._token["id_token_claims"]["email"],
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

    def list_subscriptions(self) -> dict:
        """
        List all subscriptions for user.
        """
        return self._make_microsoft_request(
            requests.get,
            MICROSOFT_SUBSCRIPTION_URI,
            headers={
                "Authorization": f"Bearer {self._token['access_token']}",
                "Content-Type": "application/json",
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

    def is_active(self, meta_data, **kwargs):
        """
        Check if the user's integration is active.

        Args:
        - meta_data: The user integration meta data.

        Returns:
        - bool: True if integration is active, False otherwise.
        """
        self._token = meta_data["token"]
        response = self.list_subscriptions()
        return "error" not in response

    @staticmethod
    def send_reply(
        meta_data: dict,
        body: str,
        reply: str,
        **kwargs,
    ):
        """
        Send a reply to a message.

        Args:
        - meta_data: The user integration meta data.
        - body: The incoming message id.
        - reply: The reply message.
        """
        client = MicrosoftService(refresh_token=meta_data["token"]["refresh_token"])
        message_id = "-".join(body.split("-")[:-1])
        response = requests.post(
            f"{MICROSOFT_READ_MAIL_URI}{message_id}/reply",
            headers={
                "Authorization": f"Bearer {client._token['access_token']}",
                "Content-Type": "application/json",
            },
            json={
                "message": {
                    "body": {
                        "contentType": "text",
                        "content": reply,
                    }
                },
            },
        )
        if response.status_code != 202:
            raise Exception(response.text)
        return response

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
