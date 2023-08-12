import logging
import traceback

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)


class LogoutView(APIView):
    def post(self, request):
        try:
            payload = request.data
            refresh_token = payload["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as err:
            logger.error(
                f"An error occurred while logging out\n{traceback.format_exc()}"
            )
            return Response(
                {"detail": "An error occurred while logging out!"},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
