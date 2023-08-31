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

    def _initialize_twilio_client(self):
        """Initialize and return the Twilio client."""
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        return Client(account_sid, auth_token)

    def _handle_exception(self, message, status=status.HTTP_500_INTERNAL_SERVER_ERROR):
        """Log the error and return a formatted response."""
        logger.error(f"{message}\n{traceback.format_exc()}")
        return Response({"detail": message}, status=status)

    def get(self, request):
        """Send OTP code to email or phone number."""
        try:
            payload = request.query_params
            input = payload.get("input")
            input_type = payload.get("input_type")
            if not input_type or not input:
                return Response(
                    {"message": "input and input_type are required!"},
                    status.HTTP_400_BAD_REQUEST,
                )
            client = self._initialize_twilio_client()
            if input_type == "email":
                send_authentication_code_email(client, input)
            else:
                send_authentication_code_phone(client, f"+{input}", True)
            return Response(
                {"detail": "Verification code has been sent!"},
                status.HTTP_201_CREATED,
            )
        except Exception as e:
            return self._handle_exception(
                e, "An error occurred while sending verification code."
            )

    def post(self, request):
        """Verify OTP code."""
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
            client = self._initialize_twilio_client()
            verification_check = self._verify_code(client, otp, input, input_type)
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
        except TwilioRestException as e:
            return self._handle_exception(
                "An error occurred while verifying verification code.",
                status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            return self._handle_exception(
                "An error occurred while verifying verification code."
            )

    def _verify_code(self, client, otp, input, input_type):
        """Helper method to verify OTP code."""
        if input_type == "email":
            verification_check = client.verify.services(
                settings.TWILLIO_VERIFY_SERVICE_ID
            ).verification_checks.create(to=input, code=otp)
        else:
            verification_check = client.verify.services(
                settings.TWILLIO_VERIFY_SERVICE_ID
            ).verification_checks.create(to=f"+{input}", code=otp)
        return verification_check
