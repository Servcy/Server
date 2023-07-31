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


class Authentication(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        """
        Send verification code to email or phone number
        ---
        parameters:
            - name: email
                description: Email address
                required: true
                type: string
            - name: phone_number
                description: Phone number
                required: true
                type: string
            - name: is_whatsapp
                description: Send verification code via WhatsApp
                required: true
                type: string
        ---
        response:
            - code: 201
                message: Verification code sent to your email & phone number
            - code: 400
                message: Email and phone number are required
            - code: 500
                message: An error occurred while sending verification code
        """
        try:
            payload = request.query_params
            email = payload.get("email", None)
            phone_number = payload.get("phone_number", None)
            is_whatsapp = payload.get("is_whatsapp", "no")
            if not phone_number or not email:
                return Response(
                    {"message": "Email and phone number are required!"},
                    status.HTTP_400_BAD_REQUEST,
                )
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            client = Client(account_sid, auth_token)
            send_authentication_code_email(client, email)
            send_authentication_code_phone(client, phone_number, is_whatsapp == "yes")
            return Response(status.HTTP_201_CREATED)
        except Exception:
            logger.error(
                f"An error occurred while sending verification code\n{traceback.format_exc()}"
            )
            return Response(
                {"message": "An error occurred while sending verification code!"},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        """
        Verify verification code
        ---
        parameters:
            - name: email
                description: Email address
                required: true
                type: string
            - name: phone_number
                description: Phone number
                required: true
                type: string
            - name: code_email
                description: Verification code sent to email
                required: true
                type: string
            - name: code_phone
                description: Verification code sent to phone number
                required: true
                type: string
            - name: is_whatsapp
                description: Is verification code via WhatsApp
                required: true
                type: boolean
        ---
        response:
            - code: 200
                message: Verification code verified
                return: JWT tokens
            - code: 400
                message: Email and phone number are required
            - code: 401
                message: Verification codes are invalid
            - code: 404
                message: Code not found
            - code: 500
                message: An error occurred while verifying verification code
        """
        try:
            payload = request.data
            email = payload.get("email", None)
            phone_number = payload.get("phone_number", None)
            code_email = payload.get("code_email", None)
            is_whatsapp = payload.get("is_whatsapp", False)
            code_phone = payload.get("code_phone", None)
            if not phone_number and not email:
                return Response(
                    {"message": "Email or phone number is required!"},
                    status.HTTP_406_NOT_ACCEPTABLE,
                )
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            client = Client(account_sid, auth_token)
            try:
                verification_email = client.verify.services(
                    settings.TWILLIO_VERIFY_SERVICE_ID
                ).verification_checks.create(
                    to=email,
                    code=code_email,
                )
            except TwilioRestException:
                send_authentication_code_email(client, email)
                logger.error(
                    f"An error occurred while accessing verification email code\n{traceback.format_exc()}"
                )
                return Response(
                    {
                        "message": "Email verification code has been used already!\nNew verification code has been sent to your email!",
                        "cause": "email",
                    },
                    status.HTTP_404_NOT_FOUND,
                )
            try:
                verification_phone = client.verify.services(
                    settings.TWILLIO_VERIFY_SERVICE_ID
                ).verification_checks.create(
                    to=f"+{phone_number}",
                    code=code_phone,
                )
            except TwilioRestException:
                send_authentication_code_phone(client, phone_number, is_whatsapp)
                logger.error(
                    f"An error occurred while accessing verification phone code\n{traceback.format_exc()}"
                )
                return Response(
                    {
                        "message": "Phone number verification code has been used already!\nNew verification code has been sent to your phone number!",
                        "cause": "phone_number",
                    },
                    status.HTTP_404_NOT_FOUND,
                )
            if (
                verification_email.status == "approved"
                and verification_phone.status == "approved"
            ):
                account_service = AccountsService(email, phone_number)
                user = account_service.create_user_account()
                refresh_token = JWTTokenSerializer.get_token(user)
                tokens = {
                    "refresh_token": str(refresh_token),
                    "access_token": str(refresh_token.access_token),
                }
                return Response(tokens, status.HTTP_200_OK)
            elif (
                verification_email.status != "approved"
                and verification_phone.status == "approved"
            ):
                return Response(
                    {"message": "Email verification code is invalid!"},
                    status.HTTP_401_UNAUTHORIZED,
                )
            elif (
                verification_email.status == "approved"
                and verification_phone.status != "approved"
            ):
                return Response(
                    {"message": "Phone number verification code is invalid!"},
                    status.HTTP_401_UNAUTHORIZED,
                )
            else:
                return Response(
                    {"message": "Verification codes are invalid!"},
                    status.HTTP_401_UNAUTHORIZED,
                )
        except Exception:
            logger.error(
                f"An error occurred while verifying verification code\n{traceback.format_exc()}"
            )
            return Response(
                {"message": "An error occurred while verifying verification code!"},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
