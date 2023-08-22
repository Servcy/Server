import logging

from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from common.responses import error_response, success_response

logger = logging.getLogger(__name__)


class LogoutView(APIView):
    def post(self, request):
        try:
            payload = request.data
            refresh_token = payload["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return success_response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return error_response(
                logger=logger,
                logger_message=f"An error occurred while logging out.",
                error_message="An error occurred while logging out!",
            )
