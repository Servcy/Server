import logging
import traceback

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from twilio.rest import Client


logger = logging.getLogger(__name__)


class Authentication(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        tags=["Authentication"],
        operation_id="Authentication - Send verification code",
    )
    def get(self, request):
        """
        Send verification code to email or phone number
        ---
        parameters:
            - name: email
                description: Email address
                required: false
                type: string
            - name: phone_number
                description: Phone number
                required: false
                type: string
            - name: is_whatsapp
                description: Send verification code via WhatsApp
                required: false
                type: string
        ---
        response:
            - code: 201
                message: Verification code sent
            - code: 400
                message: Email or phone number is required
            - code: 500
                message: An error occurred while sending verification code
        """
        try:
            payload = request.query_params
            email = payload.get("email", None)
            phone_number = payload.get("phone_number", None)
            is_whatsapp = payload.get("is_whatsapp", "no")
            receiver = email if email else phone_number
            if not receiver:
                return Response(
                    {"message": "Email or phone number is required!"},
                    status.HTTP_400_BAD_REQUEST,
                )
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            client = Client(account_sid, auth_token)
            if email:
                verification = client.verify.services(
                    settings.TWILLIO_VERIFY_SERVICE_ID
                ).verifications.create(
                    channel_configuration={
                        "template_id": settings.SENDGRID_VERIFICATION_TEMPLATE_ID,
                        "from": settings.SENDGRID_FROM_EMAIL,
                        "from_name": "Servcy",
                    },
                    to=receiver,
                    channel="email",
                )
            elif is_whatsapp == "yes":
                verification = client.verify.services(
                    settings.TWILLIO_VERIFY_SERVICE_ID
                ).verifications.create(to=f"+{receiver}", channel="whatsapp")
            else:
                verification = client.verify.services(
                    settings.TWILLIO_VERIFY_SERVICE_ID
                ).verifications.create(to=f"+{receiver}", channel="sms")
            return Response(verification.status, status.HTTP_201_CREATED)
        except Exception:
            logger.error(
                f"An error occurred while sending verification code\n{traceback.format_exc()}"
            )
            return Response(
                {"message": "An error occurred while sending verification code!"},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        tags=["Authentication"],
        operation_id="Authentication - Verify code",
    )
    def post(self, request):
        """
        Verify verification code
        ---
        parameters:
            - name: email
                description: Email address
                required: false
                type: string
            - name: phone_number
                description: Phone number
                required: false
                type: string
            - name: code
                description: Verification code
                required: true
                type: string
        ---
        response:
            - code: 200
                message: Verification code verified
            - code: 400
                message: Email or phone number is required
            - code: 500
                message: An error occurred while verifying verification code
        """
        try:
            payload = request.data
            email = payload.get("email", None)
            phone_number = payload.get("phone_number", None)
            code = payload.get("code", None)
            receiver = email if email else phone_number
            if not receiver:
                return Response(
                    {"message": "Email or phone number is required!"},
                    status.HTTP_400_BAD_REQUEST,
                )
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            client = Client(account_sid, auth_token)
            verification = client.verify.services(
                settings.TWILLIO_VERIFY_SERVICE_ID
            ).verification_checks.create(
                to=receiver,
                code=code,
            )
            return Response(verification.status, status.HTTP_200_OK)
        except Exception:
            logger.error(
                f"An error occurred while verifying verification code\n{traceback.format_exc()}"
            )
            return Response(
                {"message": "An error occurred while verifying verification code!"},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
