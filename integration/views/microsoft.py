import logging
import urllib.parse

from rest_framework import status, viewsets
from rest_framework.decorators import action

from common.exceptions import ServcyOauthCodeException
from common.responses import error_response, success_response
from integration.services.microsoft import MicrosoftService

logger = logging.getLogger(__name__)


class MicrosoftViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["put"], url_path="oauth")
    def oauth(self, request):
        try:
            code = urllib.parse.unquote(request.data["code"])
            service = MicrosoftService(code)
            subscription = service.create_subscription(
                user_id=request.user.id,
            )
            service.create_integration(
                user_id=request.user.id, subscription=subscription
            )
            return success_response(
                success_message="Successfully integrated with Outlook!",
                status=status.HTTP_200_OK,
            )
        except ServcyOauthCodeException as error:
            return error_response(
                logger=logger,
                logger_message=error.message,
                error_message="An error occurred while integrating with Outlook. Please try again later.",
            )
        except KeyError:
            return error_response(
                logger=logger,
                logger_message="KeyError occurred processing oauth request.",
                error_message="code, and scope are required!",
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="An error occurred processing oauth request.",
            )
