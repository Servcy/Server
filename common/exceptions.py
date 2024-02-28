import logging

from newrelic.agent import notice_error
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class ServcyBaseException(Exception):
    """
    Custom exception base for Servcy.
    """

    @property
    def message(self):
        return str(self)


class ServcyAPIException(APIException, ServcyBaseException):
    """
    APIException for Servcy server.
    """

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Servcy API encountered an error!"
    default_code = "APIException"


class ServcyOauthCodeException(ServcyBaseException):
    """
    Exception raised when oauth code is not provided.
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Oauth code is required!"
    default_code = "OauthCodeException"


class ExternalIntegrationException(ServcyAPIException):
    """
    For Servcy External Integrations.
    """

    default_detail = "An External Integration Exception has occurred"
    default_code = "ExternalIntegrationException"


class IntegrationAccessRevokedException(ServcyAPIException):
    """
    For Servcy External Integrations.
    """

    default_detail = "Integration access revoked"
    default_code = "IntegrationAccessRevokedException"
    status_code = status.HTTP_401_UNAUTHORIZED


def servcy_exception_handler(exception, context):
    """
    Main exception handler for Servcy.
    """
    # Structured logging
    log_data = {
        "exception_type": type(exception).__name__,
        "exception_detail": str(exception),
        "context": context,
    }
    logger.exception("An error occurred in the API.", extra=log_data, exc_info=True)

    # Notify New Relic
    notice_error(exception)

    # Use DRF's default exception handler
    response = exception_handler(exception, context)
    if response is not None:
        response.data["status_code"] = response.status_code
    return response


class ExternalAPIRateLimitException(ServcyAPIException):
    """
    For Servcy External API Rate Limit.
    """

    default_detail = "External API Rate Limit Exception"
    default_code = "ExternalAPIRateLimitException"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
