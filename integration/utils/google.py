from attrs import define
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


@define
class GoogleCredentials:
    client_id: str
    client_secret: str
    token_uri: str
    redirect_uri: str
    scopes: list[str]
    user_info_uri: str


def get_google_credentials() -> GoogleCredentials:
    """ """
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
