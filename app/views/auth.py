import logging
import traceback

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from app.utils.auth import (
    send_authentication_code_email,
    send_authentication_code_phone,
)
from iam.serializers.jwt import JWTTokenSerializer
from iam.services.accounts import AccountsService

logger = logging.getLogger(__name__)


class AuthenticationView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        """
        Send OTP code to email or phone number
        """
        try:
            payload = request.query_params
            input = payload.get("input")
            input_type = payload.get("input_type")
            if not input_type or not input:
                return Response(
                    {"message": "input and input_type are required!"},
                    status.HTTP_400_BAD_REQUEST,
                )
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            client = Client(account_sid, auth_token)
            if input_type == "email":
                send_authentication_code_email(client, input)
            else:
                send_authentication_code_phone(client, f"+{input}", True)
            return Response(
                {"detail": "Verification code has been sent!"},
                status.HTTP_201_CREATED,
            )
        except Exception:
            logger.error(
                f"An error occurred while sending verification code\n{traceback.format_exc()}"
            )
            return Response(
                {"detail": "An error occurred while sending verification code!"},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        """
        Verify OTP code
        """
        try:
            payload = request.data
            otp = payload.get("otp", None)
            input = payload.get("input", None)
            input_type = payload.get("input_type", None)
            if not otp or not input_type or not input:
                return Response(
                    {"detail": "otp, input and input_type are required!"},
                    status.HTTP_406_NOT_ACCEPTABLE,
                )
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            client = Client(account_sid, auth_token)
            if input_type == "email":
                try:
                    verification_check = client.verify.services(
                        settings.TWILLIO_VERIFY_SERVICE_ID
                    ).verification_checks.create(
                        to=input,
                        code=otp,
                    )
                except TwilioRestException:
                    logger.error(
                        f"An error occurred while accessing verification email code\n{traceback.format_exc()}"
                    )
                    return Response(
                        {
                            "detail": "Email verification code has been used already!",
                        },
                        status.HTTP_401_UNAUTHORIZED,
                    )
            else:
                try:
                    verification_check = client.verify.services(
                        settings.TWILLIO_VERIFY_SERVICE_ID
                    ).verification_checks.create(
                        to=f"+{input}",
                        code=otp,
                    )
                except TwilioRestException:
                    logger.error(
                        f"An error occurred while accessing verification phone code\n{traceback.format_exc()}"
                    )
                    return Response(
                        {
                            "detail": "Phone number verification code has been used already!",
                        },
                        status.HTTP_401_UNAUTHORIZED,
                    )
            if verification_check.status == "approved":
                account_service = AccountsService(input, input_type)
                user = account_service.create_user_account()
                refresh_token = JWTTokenSerializer.get_token(user)
                tokens = {
                    "refresh_token": str(refresh_token),
                    "access_token": str(refresh_token.access_token),
                }
                return Response(tokens, status.HTTP_200_OK)
            else:
                return Response(
                    {"detail": "Verification code is invalid!"},
                    status.HTTP_401_UNAUTHORIZED,
                )
        except Exception:
            logger.error(
                f"An error occurred while verifying verification code\n{traceback.format_exc()}"
            )
            return Response(
                {"detail": "An error occurred while verifying verification code!"},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
