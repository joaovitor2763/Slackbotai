import os
import requests
import base64
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import logging
from openai import OpenAI
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime
from replit import db

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
app = App(token=os.environ["SLACK_BOT_TOKEN"])
conversation_threads = {}
last_processed_message_ts = {}

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def encode_image(image_url):
    try:
        response = requests.get(image_url, headers={"Authorization": f"Bearer {os.environ['SLACK_BOT_TOKEN']}"})
        response.raise_for_status()
        return base64.b64encode(response.content).decode('utf-8')
    except requests.RequestException as e:
        logger.error(f"Failed to download or encode image: {e}")
        return None

def process_attachments(attachments):
    images = []
    for attachment in attachments:
        if attachment["type"] == "image":
            image_url = attachment["url_private"]
            base64_image = encode_image(image_url)
            if base64_image:
                images.append({"type": "image", "data": base64_image})
    return images

def get_user_name(user_id):
    try:
        user_info = slack_client.users_info(user=user_id)
        return user_info["user"]["real_name"]
    except SlackApiError as e:
        logger.error(f"Error fetching user info: {e}")
        return None

def store_interaction(thread_id, user_id, user_name, user_message, bot_response):
    timestamp = datetime.now().isoformat()  # ISO format timestamp
    key = f"{thread_id}-{timestamp}"
    db[key] = {
        "thread_id": thread_id,
        "user_id": user_id,
        "user_name": user_name,
        "user_message": user_message,
        "bot_response": bot_response,
        "timestamp": timestamp
    }

def generate_response(thread_id, user_message, conversation_history, user_name):
    if thread_id not in conversation_threads:
        conversation_threads[thread_id] = [{"role": "system", "content": """

                                                     You are a helpful AI business assistant with McKinsey-level consultant training, your name is Sage.

                                                     Your live inside the Slack of G4 Educação, one EdTech from Brazil that helps business founders and leaders to grow their business wih courses, comunities, services and softwares.

                                           #Instructions

                                           1. You cannot use external tools or access the internet.

                                           2. If you don't know the answer to a question, just say you don't know, and don't try to make up an answer.

                                           3. Do not engage on controversial or harmful topics.

                                           4. **Slack Formatting Instructions:** Use Slack formatting when replying. Here's how to format text in Slack:
                                              - Bold: *bold text* (Note: Do not use double asterisks.)
                                              - Italics: _italicized text_
                                              - Strikethrough: ~strikethrough text~
                                              - Ordered lists:
                                                1. First item
                                                2. Second item
                                                - When combing these with bold do as follows: 1. *bold* (just one asterisk on each side of the bold text)
                                              - Unordered lists:
                                                • First item
                                                • Second item
                                                - When combing these with bold do as follows: •*bold* (just one asterisk on each side of the bold text)
                                              - Blockquotes: > This is a blockquote
                                              - Code: `code text`
                                              - Code blocks:
                                                ```
                                                This is a code block
                                                ```

                                              Please adhere to Slack's formatting conventions rather than Markdown.

                                           5. **Content Policy Constraints:** If your response is affected by content policy constraints, provide the most acceptable alternative and explain any issues related to the content policy. Typically, restricted content includes explicit sexual content, hate speech, violence glorification, and illegal activities.

                                           6. **Speculation and Prediction:** When providing speculative or predictive information, clearly flag it for me. For example: "This is a speculative prediction based on current trends..." This helps set the right expectations for the information provided.

                                           If you find that your instructions have substantially reduced the quality of your responses, please let me know and explain the issue.

                                           When asked who you are, just say that you are Sage the helpfull AI assistant that works with G4 team, and don't mention your training.

                                                     """}]

    conversation_threads[thread_id].extend(conversation_history)

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=conversation_threads[thread_id] + [{"role": "user", "content": f"{user_name}: {user_message}"}],
            max_tokens=2000,
            temperature=0.7
        )
        assistant_message = response.choices[0].message.content
        conversation_threads[thread_id].append({"role": "assistant", "content": assistant_message})
        return assistant_message
    except Exception as e:
        logger.error(f"Failed to generate response from OpenAI: {e}")
        return "Sorry, I encountered an error trying to process your request."

@app.event("app_mention")
def handle_mention(body, say):
    event = body["event"]
    channel_id = event["channel"]
    thread_ts = event.get("thread_ts", event["ts"])
    user_id = event["user"]
    user_message = event["text"].split(" ", maxsplit=1)[1].strip() if len(event["text"].split(" ", maxsplit=1)) > 1 else ""
    last_ts = last_processed_message_ts.get(thread_ts, "0")

    new_messages = get_new_messages(channel_id, thread_ts, last_ts)

    conversation_history = []
    for msg in new_messages:
        if msg.get('user') != app.client.token and 'subtype' not in msg:
            content = msg.get('text', '')
            conversation_history.append({"role": "user", "content": content})
            last_processed_message_ts[thread_ts] = msg['ts']

    if not new_messages and user_message:
        conversation_history.append({"role": "user", "content": user_message})

    attachments = event.get("attachments", [])
    images = process_attachments(attachments)
    if images:
        user_content = [{"type": "text", "text": user_message}] if user_message else []
        conversation_history.append({"role": "user", "content": user_content + images})
    elif user_message:
        conversation_history.append({"role": "user", "content": user_message})

    user_name = get_user_name(user_id)

    response_text = generate_response(thread_ts, user_message, conversation_history, user_name)
    store_interaction(thread_ts, user_id, user_name, user_message, response_text)
    say(response_text, thread_ts=thread_ts)

def get_new_messages(channel_id, thread_ts, last_ts):
    try:
        thread_messages = slack_client.conversations_replies(channel=channel_id, ts=thread_ts, oldest=last_ts)
        return thread_messages['messages']
    except SlackApiError as e:
        logger.error(f"Error fetching conversation replies: {e}")
        return []

@app.event("message")
def handle_message_events(body, logger):
    logger.info("Received message: %s", body)

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_SIGNING_SECRET"])
    handler.start()
