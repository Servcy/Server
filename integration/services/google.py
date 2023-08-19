import requests
from attrs import define
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from google.cloud import pubsub_v1
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


@define
class GoogleCredentials:
    client_id: str
    client_secret: str
    token_uri: str
    redirect_uri: str
    scopes: list[str]
    user_info_uri: str


class GoogleService:
    @staticmethod
    def get_secrets() -> GoogleCredentials:
        """
        Get Google OAuth2 secrets from env.
        """
        client_id = settings.GOOGLE_OAUTH2_CLIENT_ID
        client_secret = settings.GOOGLE_OAUTH2_CLIENT_SECRET
        token_uri = settings.GOOGLE_OAUTH2_TOKEN_URI
        scopes = settings.GOOGLE_OAUTH2_SCOPES
        redirect_uri = settings.GOOGLE_OAUTH2_REDIRECT_URI
        user_info_uri = settings.GOOGLE_OAUTH2_USER_INFO_URI

        if not client_id:
            raise ImproperlyConfigured("GOOGLE_OAUTH2_CLIENT_ID missing in env.")

        if not client_secret:
            raise ImproperlyConfigured("GOOGLE_OAUTH2_CLIENT_SECRET missing in env.")

        if not token_uri:
            raise ImproperlyConfigured("GOOGLE_OAUTH2_TOKEN_URI missing in env.")

        if not scopes:
            raise ImproperlyConfigured("GOOGLE_OAUTH2_SCOPES missing in env.")

        if not redirect_uri:
            raise ImproperlyConfigured("GOOGLE_OAUTH2_REDIRECT_URI missing in env.")

        if not user_info_uri:
            raise ImproperlyConfigured("GOOGLE_OAUTH2_USER_INFO_URI missing in env.")

        credentials = GoogleCredentials(
            client_id=client_id,
            redirect_uri=redirect_uri,
            user_info_uri=user_info_uri,
            client_secret=client_secret,
            token_uri=token_uri,
            scopes=scopes,
        )

        return credentials

    @staticmethod
    def fetch_tokens(code: str, secrets: GoogleCredentials) -> dict:
        response = requests.post(
            secrets.token_uri,
            data={
                "code": code,
                "client_id": secrets.client_id,
                "client_secret": secrets.client_secret,
                "redirect_uri": secrets.redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        return response.json()

    @staticmethod
    def fetch_user_info(access_token: str, secrets: GoogleCredentials) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(secrets.user_info_uri, headers=headers)
        return response.json()

    @staticmethod
    def refresh_token(refresh_token: str, secrets: GoogleCredentials) -> dict:
        response = requests.post(
            secrets.token_uri,
            data={
                "refresh_token": refresh_token,
                "client_id": secrets.client_id,
                "client_secret": secrets.client_secret,
                "grant_type": "refresh_token",
            },
        )
        return response.json()

    @staticmethod
    def revoke_token(token: str, secrets: GoogleCredentials) -> dict:
        response = requests.post(
            secrets.token_uri,
            data={
                "token": token,
                "client_id": secrets.client_id,
                "client_secret": secrets.client_secret,
            },
        )
        return response.json()

    @staticmethod
    def add_watcher_to_inbox_pub_sub(
        client_id: str,
        client_secret: str,
        refresh_token: str,
        access_token: str,
        email: str,
    ) -> dict:
        """
        Add a watcher to the inbox topic.
        :param client_id: Google OAuth2 client id.
        :param client_secret: Google OAuth2 client secret.
        :param refresh_token: Google OAuth2 refresh token.
        :param access_token: Google OAuth2 access token.
        :param email: Email address of the user.
        :return: Response from Google.
            - history_id: History id of the user's inbox.
            - expiration: Expiration time of the access token.
        """
        credentials = Credentials(
            token=access_token,
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
        )
        service = build("gmail", "v1", credentials=credentials)
        watch_request = {
            "labelIds": ["INBOX"],
            "topicName": settings.GOOGLE_PUB_SUB_TOPIC,
        }
        response = service.users().watch(userId=email, body=watch_request).execute()
        return response

    @staticmethod
    def add_publisher_for_user(email: str):
        pubsub_v1_client = pubsub_v1.PublisherClient()
        policy = pubsub_v1_client.get_iam_policy(
            request={"resource": settings.GOOGLE_PUB_SUB_TOPIC}
        )
        policy.bindings.add(
            role="roles/pubsub.publisher",
            members=[f"user:{email}"],
        )
        pubsub_v1_client.set_iam_policy(
            request={"resource": settings.GOOGLE_PUB_SUB_TOPIC, "policy": policy}
        )
        return True

    @staticmethod
    def remove_publisher_for_user(email: str):
        pubsub_v1_client = pubsub_v1.PublisherClient()
        policy = pubsub_v1_client.get_iam_policy(
            request={"resource": settings.GOOGLE_PUB_SUB_TOPIC}
        )
        policy.bindings.add(
            role="roles/pubsub.publisher",
            members=[f"user:{email}"],
        )
        pubsub_v1_client.set_iam_policy(
            request={"resource": settings.GOOGLE_PUB_SUB_TOPIC, "policy": policy}
        )
        return True

    @staticmethod
    def get_history(history_id: int, tokens: dict):
        credentials = Credentials(
            token=tokens["access_token"],
            client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
            client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
            refresh_token=tokens["refresh_token"],
            token_uri=settings.GOOGLE_OAUTH2_TOKEN_URI,
        )
        gmail = build("gmail", "v1", credentials=credentials)
        results = (
            gmail.users()
            .history()
            .list(userId="me", startHistoryId=history_id)
            .execute()
        )
        return results

    @staticmethod
    def get_latest_unread_primary_inbox(
        last_message_id: str,
        tokens: dict,
    ):
        credentials = Credentials(
            token=tokens["access_token"],
            client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
            client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
            refresh_token=tokens["refresh_token"],
            token_uri=settings.GOOGLE_OAUTH2_TOKEN_URI,
        )
        service = build("gmail", "v1", credentials=credentials)
        response = (
            service.users()
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
            if message["id"] == last_message_id:
                break
            new_messages.append(message)
        return new_messages

    @staticmethod
    def get_message(message_id: str, tokens: dict):
        credentials = Credentials(
            token=tokens["access_token"],
            client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
            client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
            refresh_token=tokens["refresh_token"],
            token_uri=settings.GOOGLE_OAUTH2_TOKEN_URI,
        )
        service = build("gmail", "v1", credentials=credentials)
        response = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
            )
            .execute()
        )
        return response
