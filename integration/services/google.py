import logging

import requests
from attrs import define
from django.conf import settings
from google.cloud import pubsub_v1
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from integration.repository import IntegrationRepository

from .base import BaseService

logger = logging.getLogger(__name__)

GOOGLE_CLIENT_ID = settings.GOOGLE_OAUTH2_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_OAUTH2_CLIENT_SECRET
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_SCOPES = settings.GOOGLE_OAUTH2_SCOPES
GOOGLE_REDIRECT_URI = settings.GOOGLE_OAUTH2_REDIRECT_URI
GOOGLE_USER_INFO_URI = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_PUB_SUB_TOPIC = settings.GOOGLE_PUB_SUB_TOPIC


class GoogleService(BaseService):
    def __init__(
        self, token: str = None, refresh_token: str = None, code: str = None
    ) -> "GoogleService":
        self._google_service = None
        self._token = token
        self._refresh_token = refresh_token
        self._user_info = None
        self._token_response = None
        self._watcher_response = None
        if code:
            self._fetch_token(
                code
            )._fetch_user_info().add_publisher_for_user().add_watcher_to_inbox_pub_sub()
        if self._token and self._refresh_token:
            self._initialize_google_service()
        return self

    def _initialize_google_service(self):
        """Initialize google service"""
        self._google_service = build(
            "gmail",
            "v1",
            credentials=Credentials(
                token=self._token,
                client_id=GOOGLE_CLIENT_ID,
                client_secret=GOOGLE_CLIENT_SECRET,
                refresh_token=self._refresh_token,
                token_uri=GOOGLE_TOKEN_URI,
            ),
            cache_discovery=False,
        )

    def _fetch_token(self, code: str) -> "GoogleService":
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
            logger.error(
                f"Error in fetching tokens from Google: {response.get('error_description')}"
            )
            raise Exception(
                f"Error fetching tokens from Google: {response.get('error_description')}"
            )
        self._token = response["access_token"]
        self._refresh_token = response["refresh_token"]
        self._token_response = response
        return self

    def _make_google_request(self, method, **kwargs):
        """Helper function to make request to google api"""
        try:
            return method(**kwargs).execute()
        except HttpError as e:
            logger.error(f"Error in making request to Google API: {e}")
            raise

    def _fetch_user_info(self) -> "GoogleService":
        """Fetch user info from google"""
        self._user_info = requests.get(
            GOOGLE_USER_INFO_URI,
            headers={"Authorization": f"Bearer {self._token}"},
        ).json()
        return self

    def add_watcher_to_inbox_pub_sub(
        self,
    ) -> dict:
        """Add watcher to inbox pub sub"""
        watch_request = {
            "labelIds": ["INBOX"],
            "topicName": GOOGLE_PUB_SUB_TOPIC,
        }
        self._watcher_response = self._make_google_request(
            self._google_service.users().watch,
            userId=self._user_info["email"],
            body=watch_request,
        )

    def remove_watcher_from_inbox_pub_sub(
        self,
        email: str,
    ) -> dict:
        """Remove watcher from inbox pub sub"""
        return self._make_google_request(
            self._google_service.users().stop, userId=email
        )

    def add_publisher_for_user(self):
        """Add publisher for user"""
        pubsub_v1_client = pubsub_v1.PublisherClient()
        policy = pubsub_v1_client.get_iam_policy(
            request={"resource": GOOGLE_PUB_SUB_TOPIC}
        )
        policy.bindings.add(
            role="roles/pubsub.publisher",
            members=[f"user:{self._user_info['email']}"],
        )
        pubsub_v1_client.set_iam_policy(
            request={"resource": GOOGLE_PUB_SUB_TOPIC, "policy": policy}
        )
        return self

    @staticmethod
    def remove_publisher_for_user(email: str):
        """Remove publisher for user"""
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
                logger.error(
                    f"Error in fetching messages through batch request for google ::: {request_id} - {exception}"
                )
            else:
                messages.append(response)

        batch = self._google_service.new_batch_http_request(callback=callback)
        for message_id in message_ids:
            batch.add(
                self._google_service.users().messages().get(userId="me", id=message_id)
            )
        self._make_google_request(batch.execute)
        return messages

    def create_integration(self, user_id: int):
        if self._user_info is None:
            raise Exception("User info is required!")
        integration = IntegrationRepository.get_integration(filters={"name": "Gmail"})
        return IntegrationRepository.create_user_integration(
            integration_id=integration.id,
            user_id=user_id,
            account_id=self._user_info["email"],
            meta_data={
                **self._token_response,
                **self._user_info,
                **self._watcher_response,
            },
            account_display_name=self._user_info["email"],
        )

    def is_active(self, meta_data):
        """
        Implementation of abstract method from BaseService.
        """
        self._token = meta_data["access_token"]
        self._refresh_token = meta_data["refresh_token"]
        self._initialize_google_service()
        return True
