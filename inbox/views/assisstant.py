import logging

from django.http import StreamingHttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action

from assisstant import generate_text_stream
from common.responses import error_response
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)


class AssisstantViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(methods=["post"], detail=False, url_path="generate-reply")
    def generate_reply(self, request):
        try:
            input_text = request.data.get("input_text", "")
            if not input_text:
                return error_response(
                    error_message="Input text is required to generate reply",
                    status=400,
                )
            text_stream = generate_text_stream(
                [
                    {
                        "role": "system",
                        "content": "You're an AI assistant used by Servcy to help users write replies for their incoming messages.",
                    },
                    {
                        "role": "user",
                        "content": f"I've received following message/event/comment, help me write a reply for it.\n{input_text}",
                    },
                ],
                request.user.id,
            )
            response = StreamingHttpResponse(
                text_stream, content_type="text/event-stream", status=200
            )
            response["Cache-Control"] = "no-cache"
            return response
        except Exception as e:
            logger.error(e)
            return error_response("Error while generating reply")
