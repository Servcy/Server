import base64
import logging
import time
import traceback
from email.mime.text import MIMEText

import requests
from django.conf import settings
from google.api_core.exceptions import Aborted
from google.auth.exceptions import RefreshError
from google.cloud import pubsub_v1
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from common.exceptions import IntegrationAccessRevokedException
from document.repository import DocumentRepository
from inbox.services.google import GoogleMailService
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
    def __init__(self, code: str = None, **kwargs) -> None:
        self._google_service = None
        self._token = None
        self._user_info = None
        self._watcher_response = None
        if code:
            self._fetch_token(code)
        if kwargs.get("access_token") and kwargs.get("refresh_token"):
            self._token = {
                "access_token": kwargs["access_token"],
                "refresh_token": kwargs["refresh_token"],
            }
        if self._token:
            self._initialize_google_service()
            if code:
                self._fetch_user_info()._add_publisher_for_user()._add_watcher_to_inbox_pub_sub(
                    self._user_info["email"]
                )

    def refresh_tokens(self):
        """Refresh tokens"""
        response = requests.post(
            GOOGLE_TOKEN_URI,
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "refresh_token": self._token["refresh_token"],
                "grant_type": "refresh_token",
            },
        ).json()
        if "error" in response:
            logger.exception(
                f"Error in refreshing tokens from Google: {response.get('error_description')}"
            )
            raise Exception(
                f"Error refreshing tokens from Google: {response.get('error_description')}"
            )
        return response

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
                raise IntegrationAccessRevokedException()
            else:
                logger.exception(
                    f"Error in initializing google service: {err}",
                    extra={
                        "traceback": traceback.format_exc(),
                    },
                )
                raise Exception("Error in initializing google service")

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
            logger.exception(
                f"Error in fetching tokens from Google: {response.get('error_description')}"
            )
            raise Exception(
                f"Error fetching tokens from Google: {response.get('error_description')}"
            )
        self._token = response
        return self

    def _make_google_request(self, method, **kwargs):
        """Helper function to make request to google api"""
        try:
            return method(**kwargs).execute()
        except RefreshError:
            logger.exception(
                "Error in refreshing token for google",
                extra={
                    "user_info": self._user_info,
                    "traceback": traceback.format_exc(),
                    "token": self._token,
                },
            )
            raise IntegrationAccessRevokedException()
        except HttpError as e:
            logger.exception(
                f"Error in making request to Google API: {e}",
                extra={
                    "traceback": traceback.format_exc(),
                },
            )
            raise

    def _fetch_user_info(self) -> "GoogleService":
        """
        Fetch user info from google
        No need to refresh token as it is already done in _fetch_token
        _fetch_token should ALWAYS be called before calling this method
        """
        self._user_info = requests.get(
            GOOGLE_USER_INFO_URI,
            headers={"Authorization": f"Bearer {self._token['access_token']}"},
        ).json()
        return self

    def _fetch_user_info_from_service(self) -> "GoogleService":
        """Fetch user info from google"""
        self._user_info = self._make_google_request(
            self._google_service.users().getProfile,
            userId="me",
        )
        return self

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

    def remove_watcher_from_inbox_pub_sub(
        self,
        email: str,
    ) -> dict:
        """Remove watcher from inbox pub sub"""
        return self._make_google_request(
            self._google_service.users().stop, userId=email
        )

    def _add_publisher_for_user(self) -> "GoogleService":
        """Add publisher for user"""
        pubsub_v1_client = pubsub_v1.PublisherClient()
        max_retries = 5
        base_delay = 1  # Initial delay is 1 second

        for attempt in range(max_retries):
            try:
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
            except Aborted as e:
                # Exponential backoff
                sleep_time = base_delay * (2**attempt)
                logger.warning(
                    f"Failed to add publisher for user {self._user_info['email']}. Retrying in {sleep_time} seconds.",
                    extra={"traceback": traceback.format_exc()},
                )
                time.sleep(sleep_time)
        # If all retries failed, raise an exception
        raise Exception("Failed to add publisher for user after several retries.")

    @staticmethod
    def remove_publisher_for_user(email: str):
        """Remove publisher for user"""
        pubsub_v1_client = pubsub_v1.PublisherClient()
        max_retries = 5
        base_delay = 1  # Initial delay is 1 second
        for attempt in range(max_retries):
            try:
                policy = pubsub_v1_client.get_iam_policy(
                    request={"resource": GOOGLE_PUB_SUB_TOPIC}
                )
                # Remove the user from the bindings instead of adding
                for binding in policy.bindings:
                    if (
                        binding.role == "roles/pubsub.publisher"
                        and f"user:{email}" in binding.members
                    ):
                        binding.members.remove(f"user:{email}")

                pubsub_v1_client.set_iam_policy(
                    request={"resource": GOOGLE_PUB_SUB_TOPIC, "policy": policy}
                )
                return True
            except Aborted as e:
                # Exponential backoff
                sleep_time = base_delay * (2**attempt)
                logger.warning(
                    f"Failed to remove publisher for user {email}. Retrying in {sleep_time} seconds.",
                    extra={"traceback": traceback.format_exc(), "email": email},
                )
                time.sleep(sleep_time)
        # If all retries failed, raise an exception
        raise Exception("Failed to remove publisher for user after several retries.")

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

    def create_integration(self, user_id: int):
        if self._user_info is None:
            raise Exception("User info is required!")
        integration = IntegrationRepository.get_integration(filters={"name": "Gmail"})
        return IntegrationRepository.create_user_integration(
            integration_id=integration.id,
            user_id=user_id,
            account_id=self._user_info["email"],
            meta_data={
                "token": self._token,
                "watcher_response": self._watcher_response,
                "user_info": self._user_info,
            },
            account_display_name=self._user_info["email"],
        )

    def is_active(self, meta_data, **kwargs):
        """
        Implementation of abstract method from BaseService.
        """
        self._token = meta_data["token"]
        self._initialize_google_service()
        return True

    @staticmethod
    def send_reply(
        meta_data: dict,
        body: str,
        reply: str,
        file_ids: list[int],
        **kwargs,
    ):
        """
        Send a reply to a message.

        Args:
        - meta_data: The user integration meta data.
        - body: The incoming message id.
        - reply: The reply message.
        """
        documents = DocumentRepository.get_documents(filters={"id__in": file_ids})
        attachment_data = []
        for document in documents:
            attachment_data.append(
                {
                    "filename": document.name,
                    "data": document.file.read(),
                }
            )
        service = GoogleService(
            refresh_token=meta_data["token"]["refresh_token"],
            access_token=meta_data["token"]["access_token"],
        )
        user_integration = kwargs.get("user_integration")
        message_id = body.split(f"-{user_integration['id']}-")[0]
        mail = service.get_message(message_id)
        thread = service._make_google_request(
            service._google_service.users().threads().get,
            userId="me",
            id=mail["threadId"],
        )
        response = service._make_google_request(
            service._google_service.users().messages().send,
            userId="me",
            body=service.create_html_message(
                sender=GoogleMailService._get_mail_header(
                    "Reply-To", mail["payload"]["headers"]
                ),
                recipient=GoogleMailService._get_mail_header(
                    "From", mail["payload"]["headers"]
                ),
                cc=GoogleMailService._get_mail_header("Cc", mail["payload"]["headers"]),
                subject=GoogleMailService._get_mail_header(
                    "Subject", mail["payload"]["headers"]
                ),
                body=reply,
                threadId=thread["id"],
                in_reply_to=GoogleMailService._get_mail_header(
                    "Message-ID", mail["payload"]["headers"]
                ),
            ),
            attachments=attachment_data,
        )
        return response

    @staticmethod
    def create_html_message(
        sender: str,
        recipient: str,
        cc: str,
        subject: str,
        body: str,
        threadId: str = None,
        in_reply_to: str = None,
    ) -> dict:
        """Creates a message for an email."""
        message = MIMEText(body, "html")
        message["to"] = recipient
        if cc:
            message["cc"] = cc
        if in_reply_to:
            message["In-Reply-To"] = in_reply_to
            message["References"] = in_reply_to
        message["from"] = sender
        message["subject"] = subject
        return {
            "raw": base64.urlsafe_b64encode(message.as_bytes()).decode(),
            "threadId": threadId,
        }

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


def refresh_google_watchers_and_tokens():
    """
    Refresh watchers for all users in the system.
    """
    try:
        user_integrations = IntegrationRepository.get_user_integrations(
            {
                "integration__name": "Gmail",
            }
        )
        for user_integration in user_integrations:
            try:
                google_service = GoogleService(
                    access_token=user_integration["meta_data"]["token"]["access_token"],
                    refresh_token=user_integration["meta_data"]["token"][
                        "refresh_token"
                    ],
                )
                google_service._fetch_user_info_from_service()._add_watcher_to_inbox_pub_sub(
                    google_service._user_info["emailAddress"]
                )
                new_tokens = google_service.refresh_tokens()
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
                    f"Error in refreshing watchers for gmail for user integration {user_integration['id']}",
                    extra={
                        "traceback": traceback.format_exc(),
                    },
                )
                continue
    except Exception:
        logger.exception(
            f"Error in refreshing watchers for gmail.",
            extra={
                "traceback": traceback.format_exc(),
            },
        )
