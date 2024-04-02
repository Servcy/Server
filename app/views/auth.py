import logging

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response

from common.responses import error_response, success_response
from common.views import BaseAPIView
from iam.serializers import JWTTokenSerializer
from iam.services.accounts import AccountsService
from mails import SendGridEmail

logger = logging.getLogger(__name__)


class AuthenticationView(BaseAPIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        """Send OTP code to email or phone number."""
        try:
            if settings.DEBUG:
                return success_response(
                    success_message="Verification code has been faked for debug environment!",
                    status=status.HTTP_201_CREATED,
                )
            payload = request.query_params
            email = payload.get("input")
            if not email:
                return error_response(
                    error_message="Email is required!",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not settings.DEBUG and input not in settings.TEST_ACCOUNTS:
                otp = AccountsService(email, "email").create_login_otp()
                SendGridEmail(email).send_login_otp(otp)
            return success_response(
                success_message="Verification code has been sent!",
                status=status.HTTP_201_CREATED,
            )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="An error occurred while sending verification code.",
                error_message="An error occurred while sending verification code.",
            )

    def post(self, request):
        """Verify OTP code and SSO flow"""
        try:
            payload = request.data
            type = payload.get("type", None)
            login_success = False
            if type == "google":
                email = payload.get("email", None)
                login_success = True
            else:
                otp = payload.get("otp", None)
                email = payload.get("input", None)
                if not otp or not email:
                    return error_response(
                        error_message="otp, and email are required!",
                        status=status.HTTP_406_NOT_ACCEPTABLE,
                    )
                if not settings.DEBUG and email not in settings.TEST_ACCOUNTS:
                    login_success = AccountsService.verify_login_otp(email, otp)
                else:
                    login_success = True
            if login_success:
                account_service = AccountsService(email, "email")
                user = account_service.create_user_account()
                refresh_token = JWTTokenSerializer.get_token(user)
                tokens = {
                    "refresh_token": str(refresh_token),
                    "access_token": str(refresh_token.access_token),
                }
                return Response(tokens, status.HTTP_200_OK)
            else:
                return error_response(
                    error_message="Invalid email!",
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        except Exception:
            return error_response(
                logger=logger,
                logger_message="An error occurred while verifying verification code.",
                error_message="An error occurred while verifying verification code.",
            )
