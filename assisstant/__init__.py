from openai import OpenAI
from django.conf import settings

openai = OpenAI(settings.OPENAI_API_KEY, organization=settings.OPENAI_ORGANIZATION_ID)
model_id = settings.OPENAI_MODEL_ID
