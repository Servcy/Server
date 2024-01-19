from django.conf import settings
import openai

openai.api_key = settings.OPENAI_API_KEY
openai.organization = settings.OPENAI_ORGANIZATION_ID


def generate_text_stream(messages: list, user_id: int):
    response = openai.chat.completions.create(
        messages=messages,
        model=settings.OPENAI_MODEL_ID,
        n=1,
        stream=True,
        user=f"servcy-{user_id}",
    )
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content
