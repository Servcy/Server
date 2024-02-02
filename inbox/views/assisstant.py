import logging

from django.http import StreamingHttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from assisstant import generate_text_stream
from common.responses import error_response, success_response
from integration.repository import IntegrationRepository
from integration.utils.maps import integration_service_map

logger = logging.getLogger(__name__)


class AssisstantViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(methods=["post"], detail=False, url_path="generate-reply")
    def generate_reply(self, request):
        try:
            input_text = request.data.get("input_text", "")
            input_type = request.data.get("input_type", "message")
            if not input_text:
                return error_response(
                    error_message="Input text is required to generate reply",
                    status=400,
                )
            messages = [
                {
                    "role": "system",
                    "content": f"""You're an AI assistant used by Servcy to help users write replies for their incoming emails and messages. Some instructions for you are:\n1.) never add any links\n2.) never return add any text similar to 'here's a response: '[response]'' always return only the [response] part\n3.) {"always add hi, regards etc. at start and end of the response" if input_type == "email" else "never add hi, regards etc."}\n4.) messages can be raw text, or can be json containing additional data""",
                },
                {
                    "role": "user",
                    "content": f"I've received following {input_type}: {input_text}\nWrite a reply on my behalf.",
                },
            ]
            text_stream = generate_text_stream(
                messages,
                request.user.id,
            )
            response = StreamingHttpResponse(
                text_stream, content_type="text/event-stream", status=200
            )
            response["Cache-Control"] = "no-cache"
            return response
        except Exception as e:
            return error_response(
                "Error while generating reply", logger=logger, logger_message=str(e)
            )

    @action(methods=["post"], detail=False, url_path="send-reply")
    def send_reply(self, request):
        try:
            requesting_user = request.user
            body = request.data.get("body", "")
            reply = request.data.get("reply", "")
            user_integration_id = request.data.get("user_integration_id", None)
            is_body_html = request.data.get("is_body_html", False)
            if not body or not reply or not user_integration_id:
                return error_response(
                    error_message="body, reply and user_integration_id are required to send reply",
                    status=400,
                )
            user_integration = IntegrationRepository.get_user_integrations(
                filters={"id": user_integration_id, "user_id": requesting_user.id},
                first=True,
                decrypt_meta_data=True,
            )
            if not user_integration:
                return error_response(
                    error_message="No user integration found, please make sure that integration hasn't been revoked.",
                    status=400,
                    logger=logger,
                    logger_message="No user integration found for given id",
                )
            service_class = integration_service_map.get(
                user_integration["integration__name"]
            )
            if service_class is None:
                raise ValueError(
                    f"Integration '{user_integration['integration__name']}' is not supported."
                )
            service_class.send_reply(
                meta_data=user_integration["meta_data"],
                user_integration=user_integration,
                body=body,
                reply=reply,
                is_body_html=is_body_html,
            )
            return success_response()
        except Exception as e:
            return error_response(
                "Error while sending reply", logger=logger, logger_message=str(e)
            )
