import logging

from openai import OpenAI

from src.settings import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(level=logging.ERROR)

logger = logging.getLogger(__name__)


def get_assistant_message(conversation_threads, thread_id, user_message, user_name):
    model = 'gpt-3.5-turbo' #gpt-4-turbo
    response = client.chat.completions.create(
        model=model,
        messages=conversation_threads[thread_id] + [{"role": "user", "content": f"{user_name}: {user_message}"}],
        max_tokens=2000,
        temperature=0.7
    )
    assistant_message = response.choices[0].message.content
    conversation_threads[thread_id].append({"role": "assistant", "content": assistant_message})
    return assistant_message
