import logging

from openai import OpenAI

from src.settings import (
    OPENAI_API_KEY,
    OPENAI_API_CODE_INTERPRETER_NAME,
    OPENAI_API_CODE_INTERPRETER_INSTRUCTIONS,
    OPENAI_API_CODE_INTERPRETER_THREAD_CONTENT
)

client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(level=logging.ERROR)

logger = logging.getLogger(__name__)


# https://platform.openai.com/docs/assistants/overview?context=without-streaming

def get_assistant_message_code_interpreter(processed_files, conversation_threads, thread_id, user_message, user_name):

    messages = conversation_threads[thread_id] + [{'role': 'user', 'content': f'{user_name}: {user_message}'}]
    model = 'gpt-4-turbo'
    max_tokens = 2000
    name = OPENAI_API_CODE_INTERPRETER_NAME
    instructions = OPENAI_API_CODE_INTERPRETER_INSTRUCTIONS

    processed_file = processed_files[0]

    file = client.files.create(
        file=open(processed_file, 'rb'),
        purpose='assistants',
    )

    assistant = client.beta.assistants.create(
        name=name,
        instructions=instructions,
        tools=[{'type': 'code_interpreter'}],
        tool_resources={
            'code_interpreter': {
                'file_ids': [file.id]
            }
        },
        model=model,
        temperature=0.7,
    )

    thread = client.beta.threads.create(
        messages=[
            {
            "role": "user",
            "content": OPENAI_API_CODE_INTERPRETER_THREAD_CONTENT,
            }
        ]
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions=user_message,
    )

    assistant_message_list = []

    if run.status == 'completed': 
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for message in messages:
            try:
                content_list = message.content
                for content in content_list:
                    if 'TextContentBlock' in str(type(content)):
                        text = content.text.value
                        assistant_message_list.append(text)
            except Exception as e:
                pass
    else:
        print(run.status)

    if len(assistant_message_list) == 0:
        assistant_message_list.append('Nenhuma resposta da OpenAi ou nenhuma resposta em texto.')

    assistant_message = assistant_message_list[0]

    conversation_threads[thread_id].append({'role': 'assistant', 'content': assistant_message})

    return assistant_message
