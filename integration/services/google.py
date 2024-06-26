import logging
import time

import requests
from django.conf import settings
from google.auth.exceptions import RefreshError
from google.cloud import pubsub_v1
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from common.exceptions import (
    ExternalAPIRateLimitException,
    IntegrationAccessRevokedException,
)
from integration.repository import IntegrationRepository

from .base import BaseService

logger = logging.getLogger(__name__)

GOOGLE_CLIENT_ID = settings.GOOGLE_OAUTH2_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_OAUTH2_CLIENT_SECRET
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_SCOPES = settings.GOOGLE_OAUTH2_SCOPES
GOOGLE_USER_INFO_URI = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_PUB_SUB_TOPIC = settings.GOOGLE_PUB_SUB_TOPIC
GOOGLE_REDIRECT_URI = settings.GOOGLE_OAUTH2_REDIRECT_URI


class GoogleService(BaseService):
    def __init__(self, code: str = None, **kwargs) -> None:
        self._google_service = None
        self._token = None
        self._user_info = None
        self._watcher_response = None
        if kwargs.get("access_token") and kwargs.get("refresh_token"):
            self._token = {
                "access_token": kwargs["access_token"],
                "refresh_token": kwargs["refresh_token"],
            }
        if kwargs.get("user_info"):
            self._user_info = kwargs["user_info"]
        if code:
            self._fetch_token(code)
            self._fetch_user_info()
            GoogleService.add_publisher_to_topic(self._user_info["email"])
        if self._token:
            self._initialize_google_service()
        if code:
            self._add_watcher_to_inbox_pub_sub(self._user_info["email"])

    def _initialize_google_service(self):
        """Initialize google service"""
        try:
            self._google_service = build(
                "gmail",
                "v1",
                credentials=Credentials(
                    token=self._token["access_token"],
                    client_id=GOOGLE_CLIENT_ID,
                    client_secret=GOOGLE_CLIENT_SECRET,
                    refresh_token=self._token["refresh_token"],
                    token_uri=GOOGLE_TOKEN_URI,
                ),
                cache_discovery=False,
            )
        except HttpError as err:
            if err.resp.status == 401:
                GoogleService.remove_publisher_from_topic(self._user_info["email"])
                raise IntegrationAccessRevokedException(
                    "Access revoked for google integration"
                )
            else:
                raise err

    def _fetch_token(self, code: str):
        """Fetch tokens from google using code"""
        response = requests.post(
            GOOGLE_TOKEN_URI,
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        ).json()
        if "error" in response:
            logger.exception(
                f"Error in fetching tokens from Google: {response.get('error_description')}"
            )
            raise Exception(
                f"Error fetching tokens from Google: {response.get('error_description')}"
            )
        self._token = response

    def _make_google_request(self, method, **kwargs):
        """Helper function to make request to google api"""
        try:
            return method(**kwargs).execute()
        except RefreshError:
            GoogleService.remove_publisher_from_topic(self._user_info["email"])
            raise IntegrationAccessRevokedException(
                "Access revoked for google integration"
            )
        except HttpError as err:
            if err.resp.status == 429:
                raise ExternalAPIRateLimitException("Too many requests to google api")
            raise err

    def _fetch_user_info(self):
        """
        Fetch user info from google
        No need to refresh token as it is already done in _fetch_token
        _fetch_token should ALWAYS be called before calling this method
        """
        self._user_info = requests.get(
            GOOGLE_USER_INFO_URI,
            headers={"Authorization": f"Bearer {self._token['access_token']}"},
        ).json()

    def _add_watcher_to_inbox_pub_sub(self, email: str = None) -> dict:
        """Add watcher to inbox pub sub"""
        if not email:
            raise Exception("Email is required for adding watcher to inbox pub sub!")
        watch_request = {
            "labelIds": ["CATEGORY_PERSONAL", "INBOX", "UNREAD"],
            "topicName": GOOGLE_PUB_SUB_TOPIC,
        }
        self._watcher_response = self._make_google_request(
            self._google_service.users().watch,
            userId=email,
            body=watch_request,
        )

    def create_integration(self, user_id: int):
        if self._user_info is None:
            raise Exception("User info is required!")
        integration = IntegrationRepository.get_integration(filters={"name": "Gmail"})
        return IntegrationRepository.create_user_integration(
            integration_id=integration.id,
            user_id=user_id,
            account_id=self._user_info["email"],
            configuration={
                "whitelisted_emails": ["*@*"],
            },
            meta_data={
                "token": self._token,
                "user_info": self._user_info,
                "last_history_id": (
                    0
                    if self._watcher_response is None
                    or "historyId" not in self._watcher_response
                    else self._watcher_response["historyId"]
                ),
                "watcher_expiration": (
                    None
                    if self._watcher_response is None
                    or "expiration" not in self._watcher_response
                    else self._watcher_response["expiration"]
                ),
            },
            account_display_name=self._user_info["email"],
        )

    def is_active(self, meta_data, **kwargs):
        """
        Implementation of abstract method from BaseService.
        """
        self._user_info = meta_data["user_info"]
        self._watcher_response = {
            "historyId": meta_data.get("last_history_id", 0),
            "expiration": meta_data.get("watcher_expiration"),
        }
        self._token = {
            **meta_data["token"],
            **GoogleService.refresh_tokens(meta_data["token"]["refresh_token"]),
        }
        self._initialize_google_service()
        watcher_expiration = meta_data.get("watcher_expiration")
        if watcher_expiration and int(watcher_expiration) - 86400 < time.time():
            self._add_watcher_to_inbox_pub_sub(self._user_info["email"])
        IntegrationRepository.update_user_integraion(
            user_integration_id=kwargs["user_integration_id"],
            meta_data=IntegrationRepository.encrypt_meta_data(
                {
                    **meta_data,
                    "token": self._token,
                    "last_history_id": (
                        0
                        if self._watcher_response is None
                        or "historyId" not in self._watcher_response
                        else self._watcher_response["historyId"]
                    ),
                    "watcher_expiration": (
                        None
                        if self._watcher_response is None
                        or "expiration" not in self._watcher_response
                        else self._watcher_response["expiration"]
                    ),
                }
            ),
        )
        return True

    def get_latest_unread_primary_inbox(self, last_history_id: int) -> list[str]:
        """Get latest unread primary inbox messages"""
        response = self._make_google_request(
            self._google_service.users().history().list,
            userId="me",
            startHistoryId=last_history_id,
            historyTypes=["messageAdded"],
            labelId="UNREAD",
        )
        message_ids = []
        for history in response.get("history", []):
            messages_added = history.get("messagesAdded", [])
            for message_added in messages_added:
                message = message_added["message"]
                message_ids.append(message["id"])
        return message_ids

    def get_message(self, message_id: str):
        """Get message"""
        return self._make_google_request(
            self._google_service.users().messages().get, userId="me", id=message_id
        )

    def get_messages(self, message_ids: list[str]) -> list[dict]:
        """Get messages"""
        messages = []
        if not message_ids:
            return messages

        def callback(request_id, response, exception):
            if exception is not None:
                logger.exception(
                    f"Error in fetching messages through batch request for google ::: {request_id} - {exception}"
                )
            else:
                messages.append(response)

        batch = self._google_service.new_batch_http_request(callback=callback)
        for message_id in message_ids:
            batch.add(
                self._google_service.users().messages().get(userId="me", id=message_id)
            )
        batch.execute()
        return messages

    def get_attachments(self, attachments) -> list[dict]:
        """Get attachments"""
        attachment_data = {}
        for inbox_item_uid in attachments.keys():
            for attachment in attachments.get(inbox_item_uid, []):
                if inbox_item_uid not in attachment_data:
                    attachment_data[inbox_item_uid] = []
                file_info = self._make_google_request(
                    self._google_service.users().messages().attachments().get,
                    userId="me",
                    messageId=attachment["message_id"],
                    id=attachment["attachment_id"],
                )
                attachment_data[inbox_item_uid].append(
                    {
                        "name": attachment["filename"],
                        "data": file_info["data"],
                    }
                )
            return attachment_data

    @staticmethod
    def add_publisher_to_topic(email: str):
        """Add publisher for user"""
        try:
            pubsub_v1_client = pubsub_v1.PublisherClient()
            policy = pubsub_v1_client.get_iam_policy(
                request={"resource": GOOGLE_PUB_SUB_TOPIC}
            )
            policy.bindings.add(
                role="roles/pubsub.publisher",
                members=[f"user:{email}"],
            )
            pubsub_v1_client.set_iam_policy(
                request={"resource": GOOGLE_PUB_SUB_TOPIC, "policy": policy}
            )
        except:
            pass

    @staticmethod
    def remove_publisher_from_topic(email: str):
        """Remove publisher for user"""
        try:
            pubsub_v1_client = pubsub_v1.PublisherClient()
            policy = pubsub_v1_client.get_iam_policy(
                request={"resource": GOOGLE_PUB_SUB_TOPIC}
            )
            for binding in policy.bindings:
                if (
                    binding.role == "roles/pubsub.publisher"
                    and f"user:{email}" in binding.members
                ):
                    binding.members.remove(f"user:{email}")
            pubsub_v1_client.set_iam_policy(
                request={"resource": GOOGLE_PUB_SUB_TOPIC, "policy": policy}
            )
        except:
            pass

    @staticmethod
    def refresh_tokens(refresh_token):
        """Refresh tokens"""
        response = requests.post(
            GOOGLE_TOKEN_URI,
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        if "error" in response.json():
            response.raise_for_status()
        return response.json()
