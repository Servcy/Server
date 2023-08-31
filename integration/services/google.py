import logging

import requests
from attrs import define
from django.conf import settings
from google.cloud import pubsub_v1
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

GOOGLE_CLIENT_ID = settings.GOOGLE_OAUTH2_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_OAUTH2_CLIENT_SECRET
GOOGLE_TOKEN_URI = settings.GOOGLE_OAUTH2_TOKEN_URI
GOOGLE_SCOPES = settings.GOOGLE_OAUTH2_SCOPES
GOOGLE_REDIRECT_URI = settings.GOOGLE_OAUTH2_REDIRECT_URI
GOOGLE_USER_INFO_URI = settings.GOOGLE_OAUTH2_USER_INFO_URI
GOOGLE_PUB_SUB_TOPIC = settings.GOOGLE_PUB_SUB_TOPIC


@define
class GoogleCredentials:
    client_id: str
    client_secret: str
    token_uri: str
    redirect_uri: str
    scopes: list[str]
    user_info_uri: str


class GoogleService:
    def __init__(self, token: str = None, refresh_token: str = None):
        self._google_service = None
        self.token = token
        self.refresh_token = refresh_token
        if self.token and self.refresh_token:
            self._initialize_google_service()

    def _initialize_google_service(self):
        """Initialize google service"""
        self._google_service = build(
            "gmail",
            "v1",
            credentials=Credentials(
                token=self.token,
                client_id=GOOGLE_CLIENT_ID,
                client_secret=GOOGLE_CLIENT_SECRET,
                refresh_token=self.refresh_token,
                token_uri=GOOGLE_TOKEN_URI,
            ),
            cache_discovery=False,
        )

    def close(self):
        """Close google service"""
        if self._google_service:
            self._google_service.close()

    @staticmethod
    def fetch_tokens(code: str) -> dict:
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
        )
        response_json = response.json()
        if "error" in response_json:
            logger.error(
                f"Error in fetching tokens from Google: {response_json.get('error_description')}"
            )
            raise Exception(
                f"Error fetching tokens from Google: {response_json.get('error_description')}"
            )
        return response_json

    def _make_google_request(self, method, **kwargs):
        """Helper function to make request to google api"""
        try:
            return method(**kwargs).execute()
        except HttpError as e:
            logger.error(f"Error in making request to Google API: {e}")
            raise

    def fetch_user_info(self) -> dict:
        """Fetch user info from google"""
        response = requests.get(
            self.user_info_uri,
            headers={"Authorization": f"Bearer {self.token}"},
        )
        return response.json()

    def add_watcher_to_inbox_pub_sub(
        self,
        email: str,
    ) -> dict:
        """Add watcher to inbox pub sub"""
        watch_request = {
            "labelIds": ["INBOX"],
            "topicName": self.pub_sub_topic,
        }
        response = (
            self._google_service.users()
            .watch(userId=email, body=watch_request)
            .execute()
        )
        return response

    def remove_watcher_from_inbox_pub_sub(
        self,
        email: str,
    ) -> dict:
        """Remove watcher from inbox pub sub"""
        return self._make_google_request(
            self._google_service.users().stop, userId=email
        )

    @staticmethod
    def add_publisher_for_user(email: str):
        """Add publisher for user"""
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
        batch.execute()
        return messages
