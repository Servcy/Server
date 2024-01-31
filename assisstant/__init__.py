from django.conf import settings
import openai
from tiktoken import encoding_for_model

openai.api_key = settings.OPENAI_API_KEY
openai.organization = settings.OPENAI_ORGANIZATION_ID


def get_all_tokens(messages: dict) -> list:
    """Get the total number of tokens from a list of messages"""
    tokenizer = encoding_for_model(settings.OPENAI_MODEL_ID)
    content = ""
    for message in messages:
        content += message.get("content", "")
    return tokenizer.encode(content, allowed_special="all")


def validate_token_limit(messages: dict, maximum_tokens_for_reply: int) -> list:
    """
    Validate the token limit of the messages and trim the messages if needed
    """
    tokenizer = encoding_for_model(settings.OPENAI_MODEL_ID)
    model_max_tokens = settings.OPENAI_MAX_TOKENS
    token_padding_for_encoding = 250
    allowed_tokens = (
        model_max_tokens - token_padding_for_encoding - maximum_tokens_for_reply
    )
    excess_tokens = len(get_all_tokens(messages)) - allowed_tokens
    message_index_to_trim = 0
    while (
        excess_tokens > 0
        and len(messages) > 1
        and message_index_to_trim < len(messages)
    ):
        role = messages[message_index_to_trim].get("role", "")
        if role == "system":
            # we don't trim system messages
            message_index_to_trim += 1
            continue
        message_tokens = get_all_tokens([messages[message_index_to_trim]])
        # if excess tokens can be removed by trimming this message, we trim it and return
        if len(message_tokens) > excess_tokens:
            tokens_to_remove = len(message_tokens) - excess_tokens
            messages[message_index_to_trim]["content"] = tokenizer.decode(
                message_tokens[:tokens_to_remove]
            )
            break
        # else if the message needs to be removed completely, we remove it and continue
        messages.pop(message_index_to_trim)
        excess_tokens -= len(message_tokens)
        message_index_to_trim += 1
    return messages


def generate_text_stream(messages: list, user_id: int):
    response = openai.chat.completions.create(
        messages=validate_token_limit(messages, 500),
        model=settings.OPENAI_MODEL_ID,
        n=1,
        stream=True,
        user=f"servcy-{user_id}",
    )
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content
