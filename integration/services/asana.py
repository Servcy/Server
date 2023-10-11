import requests
from django.conf import settings

from common.exceptions import ServcyOauthCodeException
from integration.models import UserIntegration
from integration.repository import IntegrationRepository


class AsanaService:
    _token_uri = "https://app.asana.com/-/oauth_token"
    _api_uri = "https://app.asana.com/api/1.0"

    """Service class for Asana integration."""

    def __init__(self, **kwargs) -> None:
        """Initializes AsanaService."""
        self._token = None
        self._user_info = None
        if kwargs.get("code"):
            self.authenticate(kwargs.get("code"))
            self._establish_webhook()

    def authenticate(self, code: str) -> "AsanaService":
        """Authenticate using code."""
        self._fetch_token(code)
        self._user_info = self._fetch_user_info()
        return self

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Helper function to make requests to Asana API."""
        url = (
            f"{AsanaService._api_uri}/{endpoint}"
            if "asana.com" not in endpoint
            else endpoint
        )
        response = requests.request(method, url, **kwargs)
        json_response = response.json()
        if "error" in json_response:
            error_msg = f"An error occurred while communicating with Asana API.\n{str(json_response)}"
            raise ServcyOauthCodeException(error_msg)
        return json_response

    def _fetch_token(self, code: str) -> None:
        """Fetches access token from Asana."""
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.ASANA_APP_CLIENT_ID,
            "client_secret": settings.ASANA_APP_CLIENT_SECRET,
            "redirect_uri": settings.ASANA_APP_REDIRECT_URI,
            "code": code,
        }
        response = requests.post(AsanaService._token_uri, data=data)
        token_data = response.json()
        if "error" in token_data:
            raise ServcyOauthCodeException(
                f"An error occurred while obtaining access token from Asana.\n{str(token_data)}"
            )
        self._token = token_data

    def _fetch_user_info(self) -> dict:
        """Fetches user info from Asana."""
        return self._make_request(
            "GET",
            "users/me",
            headers={
                "Authorization": f"Bearer {self._token['access_token']}",
                "Accept": "application/json",
            },
        )

    def _establish_webhook(self) -> None:
        """Establishes webhook for Asana."""
        self.webhook = self._make_request(
            "POST",
            f"webhooks",
            data={
                "resource": self._user_info["data"]["id"],
                "target": settings.ASANA_APP_WEBHOOK_URL,
            },
            headers={
                "Authorization": f"Bearer {self._token['access_token']}",
                "Accept": "application/json",
            },
        )

    def create_integration(self, user_id: int) -> UserIntegration:
        """Creates integration for user."""
        return IntegrationRepository.create_user_integration(
            integration_id=IntegrationRepository.get_integration(
                filters={"name": "Asana"}
            ).id,
            user_id=user_id,
            account_id=self._user_info["data"]["gid"],
            meta_data={"token": self._token, "user_info": self._user_info},
            account_display_name=self._user_info["data"]["name"],
            configuration=self.webhook,
        )
