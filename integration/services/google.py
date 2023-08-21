import logging

import requests
from attrs import define
from django.conf import settings
from google.cloud import pubsub_v1
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


@define
class GoogleCredentials:
    client_id: str
    client_secret: str
    token_uri: str
    redirect_uri: str
    scopes: list[str]
    user_info_uri: str


class GoogleService:
    client_id = settings.GOOGLE_OAUTH2_CLIENT_ID
    client_secret = settings.GOOGLE_OAUTH2_CLIENT_SECRET
    token_uri = settings.GOOGLE_OAUTH2_TOKEN_URI
    scopes = settings.GOOGLE_OAUTH2_SCOPES
    redirect_uri = settings.GOOGLE_OAUTH2_REDIRECT_URI
    user_info_uri = settings.GOOGLE_OAUTH2_USER_INFO_URI
    pub_sub_topic = settings.GOOGLE_PUB_SUB_TOPIC

    def __init__(self, token: str = None, refresh_token: str = None):
        self._google_service = None
        self.token = token
        self.refresh_token = refresh_token
        if self.token and self.refresh_token:
            self._google_service = build(
                "gmail",
                "v1",
                credentials=Credentials(
                    token=self.token,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    refresh_token=self.refresh_token,
                    token_uri=self.token_uri,
                ),
                cache_discovery=False,
            )

    def __del__(self):
        self._google_service.close()

    @classmethod
    def fetch_tokens(cls, code: str) -> dict:
        response = requests.post(
            cls.token_uri,
            data={
                "code": code,
                "client_id": cls.client_id,
                "client_secret": cls.client_secret,
                "redirect_uri": cls.redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        return response.json()

    def fetch_user_info(self) -> dict:
        response = requests.get(
            self.user_info_uri,
            headers={"Authorization": f"Bearer {self.token}"},
        )
        return response.json()

    def add_watcher_to_inbox_pub_sub(
        self,
        email: str,
    ) -> dict:
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

    @classmethod
    def add_publisher_for_user(cls, email: str):
        pubsub_v1_client = pubsub_v1.PublisherClient()
        policy = pubsub_v1_client.get_iam_policy(
            request={"resource": cls.pub_sub_topic}
        )
        policy.bindings.add(
            role="roles/pubsub.publisher",
            members=[f"user:{email}"],
        )
        pubsub_v1_client.set_iam_policy(
            request={"resource": cls.pub_sub_topic, "policy": policy}
        )
        return True

    @classmethod
    def remove_publisher_for_user(cls, email: str):
        pubsub_v1_client = pubsub_v1.PublisherClient()
        policy = pubsub_v1_client.get_iam_policy(
            request={"resource": cls.pub_sub_topic}
        )
        policy.bindings.add(
            role="roles/pubsub.publisher",
            members=[f"user:{email}"],
        )
        pubsub_v1_client.set_iam_policy(
            request={"resource": cls.pub_sub_topic, "policy": policy}
        )
        return True

    def get_latest_unread_primary_inbox(
        self,
        last_known_message_id: str,
    ):
        response = (
            self._google_service.users()
            .messages()
            .list(
                userId="me",
                labelIds=["INBOX"],
                q="is:unread category:primary",
            )
            .execute()
        )
        messages = list(response.get("messages", []))
        new_messages = []
        for message in messages:
            if message["id"] == last_known_message_id:
                break
            new_messages.append(message)
        return new_messages

    def get_message(self, message_id: str):
        response = (
            self._google_service.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
            )
            .execute()
        )
        return response

    def get_messages_with_data(self, message_ids: list[str]) -> list[dict]:
        """
        Batch request for messages
        :return: list of messages with data
        """
        messages = []
        if not message_ids:
            return messages

        def callback(request_id, response, exception):
            if exception is not None:
                logger.error(
                    f"Error in fetching messages through batch request for google ::: {request_id}\n{exception}"
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
