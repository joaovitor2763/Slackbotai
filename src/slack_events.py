from .slack_web_client import get_user_name, get_new_messages
from .openai_core import generate_response


def handle_mention(body, say, app, conversation_threads, last_processed_message_ts):

    event = body['event']
    channel_id = event['channel']
    thread_ts = event.get('thread_ts', event['ts'])
    user_id = event['user']
    user_message = event['text'].split(" ", maxsplit=1)[1].strip() if len(event['text'].split(' ', maxsplit=1)) > 1 else ''
    last_ts = last_processed_message_ts.get(thread_ts, '0')

    new_messages = get_new_messages(channel_id, thread_ts, last_ts)

    conversation_history = []
    for msg in new_messages:
        if msg.get('user') != app.client.token and 'subtype' not in msg:
            content = msg.get('text', '')
            conversation_history.append({'role': 'user', 'content': content})
            last_processed_message_ts[thread_ts] = msg['ts']

    if not new_messages and user_message:
        conversation_history.append({'role': 'user', 'content': user_message})

    files = event.get('files', [])
    user_name = get_user_name(user_id)
    response_text = generate_response(conversation_threads, files, thread_ts, user_message, conversation_history, user_name)
    # store_interaction(thread_ts, user_id, user_name, user_message, response_text)
    say(response_text, thread_ts=thread_ts)
