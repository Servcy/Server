import logging
from datetime import datetime, timedelta

import msal
import requests
from django.conf import settings

from common.exceptions import ServcyOauthCodeException
from integration.repository import IntegrationRepository

logger = logging.getLogger(__name__)


class MicrosoftService:
    client_id = settings.MICROSOFT_APP_CLIENT_ID
    client_secret_id = settings.MICROSOFT_APP_CLIENT_SECRET_ID
    scopes = settings.MICROSOFT_OAUTH2_SCOPES
    redirect_uri = settings.MICROSOFT_APP_REDIRECT_URI
    client_secret = settings.MICROSOFT_APP_CLIENT_SECRET
    read_mail_uri = "https://graph.microsoft.com/v1.0/me/messages/"
    subscription_uri = "https://graph.microsoft.com/v1.0/subscriptions/"
    authority_uri = "https://login.microsoftonline.com/common"

    @staticmethod
    def future_date_in_iso_formate(days: int, with_microseconds: bool = False) -> str:
        """
        Function to get date in future in ISO format
        """
        future_date = datetime.now() + timedelta(days=days)
        date_format = "%Y-%m-%dT%H:%M:%SZ"
        if with_microseconds:
            date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        return datetime.strftime(future_date, date_format)

    def __init__(
        self,
        code: str = None,
        refresh_token: str = None,
        scopes: list = ["User.Read", "Mail.Read"],
    ) -> None:
        self._app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority_uri,
        )
        if code:
            self._exchange_code_with_token(code)
        elif refresh_token:
            self._token = self._fetch_new_token(
                refresh_token=refresh_token,
                scopes=scopes,
            )

    def _exchange_code_with_token(
        self,
        code: str,
    ) -> None:
        """
        Exchange code for access token and refresh token.
        """
        self._token = self._app.acquire_token_by_authorization_code(
            code=code,
            scopes=["User.Read", "Mail.Read"],
            redirect_uri=self.redirect_uri,
        )
        if "error" in self._token:
            raise ServcyOauthCodeException(
                f"An error occurred while obtaining access token from Microsoft.\n{str(self._token)}"
            )

    def _fetch_new_token(
        self, refresh_token: str, scopes: list = ["User.Read", "Mail.Read"]
    ) -> dict:
        """
        Function to get new token using refresh token
        """
        return self._app.acquire_token_by_refresh_token(
            refresh_token=refresh_token,
            scopes=scopes,
        )

    def create_integration(self, user_id: int, subscription: dict) -> None:
        """
        Create integration for user.
        """
        integration = IntegrationRepository.get_integration(filters={"name": "Outlook"})
        email = self._token["id_token_claims"]["email"]
        IntegrationRepository.create_user_integration(
            integration_id=integration.id,
            user_id=user_id,
            account_id=email,
            meta_data={"token": self._token, "subscription": subscription},
        )

    def create_subscription(self, user_id: int) -> str:
        """
        Create subscription for user to receive notifications for new emails.
        :return: subscription id
        """
        response = requests.post(
            self.subscription_uri,
            headers={
                "Authorization": f"Bearer {self._token['access_token']}",
                "Content-Type": "application/json",
            },
            json={
                "changeType": "created",
                "notificationUrl": f"{settings.BACKEND_URL}/inbox/webhook/microsoft",
                "resource": "me/mailFolders('Inbox')/messages?$filter=isRead eq false",
                "expirationDateTime": MicrosoftService.future_date_in_iso_formate(
                    3, True
                ),
                "clientState": self._token["id_token_claims"]["email"],
                "includeResourceData": True,
            },
        ).json()
        if (
            "error" in response
            and response["error"]["code"] == "InvalidAuthenticationToken"
        ):
            self._token = self._fetch_new_token(
                refresh_token=self._token["refresh_token"],
                scopes=["User.Read", "Mail.Read"],
            )
            self.create_subscription(user_id)
        elif "error" in response:
            logger.error(
                f"An error occurred while creating subscription for user {user_id}.\n{str(response)}"
            )
        return response

    def renew_subscription(self, subscription_id: str) -> None:
        """
        Update subscription expiration date
        """
        response = requests.patch(
            f"{self.subscription_uri}/{subscription_id}",
            headers={
                "Authorization": f"Bearer {self._token['access_token']}",
                "Content-Type": "application/json",
            },
            json={
                "expirationDateTime": MicrosoftService.future_date_in_iso_formate(
                    3, True
                ),
            },
        ).json()
        if (
            "error" in response
            and response["error"]["code"] == "InvalidAuthenticationToken"
        ):
            self._token = self._fetch_new_token(
                refresh_token=self._token["refresh_token"],
                scopes=["User.Read", "Mail.Read"],
            )
            self.renew_subscription(subscription_id)
        elif "error" in response:
            logger.error(
                f"An error occurred while renewing subscription {subscription_id}.\n{str(response)}"
            )

    def get_message(self, message_id: str) -> dict:
        """
        Function to fetch mail from outlook with ID
        """
        response = requests.get(
            f"{self.read_mail_uri}/{message_id}",
            headers={
                "Authorization": "Bearer {}".format(self._token["access_token"]),
            },
        ).json()
        if (
            "error" in response
            and response["error"]["code"] == "InvalidAuthenticationToken"
        ):
            self._token = self._fetch_new_token(
                refresh_token=self._token["refresh_token"],
                scopes=["User.Read", "Mail.Read"],
            )
            self.get_message(message_id)
        elif "error" in response:
            logger.error(
                f"An error occurred while fetching message {message_id}.\n{str(response)}"
            )
        return response
