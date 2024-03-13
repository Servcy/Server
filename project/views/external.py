from django.conf import settings
from openai import OpenAI
from rest_framework import status
from rest_framework.response import Response

from common.permissions import ProjectEntityPermission
from common.views import BaseAPIView
from iam.models import Workspace
from iam.serializers import WorkspaceLiteSerializer
from project.models import Project
from project.serializers import ProjectLiteSerializer


class GPTIntegrationEndpoint(BaseAPIView):
    permission_classes = [
        ProjectEntityPermission,
    ]

    def post(self, request, slug, project_id):
        prompt = request.data.get("prompt", False)
        task = request.data.get("task", False)
        if not task:
            return Response(
                {"error": "Task is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        final_text = task + "\n" + prompt
        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
        )
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL_ID,
            messages=[{"role": "user", "content": final_text}],
        )
        workspace = Workspace.objects.get(slug=slug)
        project = Project.objects.get(pk=project_id)
        text = response.choices[0].message.content.strip()
        text_html = text.replace("\n", "<br/>")
        return Response(
            {
                "response": text,
                "response_html": text_html,
                "project_detail": ProjectLiteSerializer(project).data,
                "workspace_detail": WorkspaceLiteSerializer(workspace).data,
            },
            status=status.HTTP_200_OK,
        )
