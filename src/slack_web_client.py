import logging

from slack_sdk.errors import SlackApiError
from slack_sdk import WebClient

from src.settings import SLACK_BOT_TOKEN

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

slack_client = WebClient(token=SLACK_BOT_TOKEN)


def get_user_name(user_id):
    try:
        user_info = slack_client.users_info(user=user_id)
        return user_info['user']['real_name']
    except SlackApiError as e:
        logger.error(f'Error fetching user info: {e}')
        return None


def get_new_messages(channel_id, thread_ts, last_ts):
    try:
        thread_messages = slack_client.conversations_replies(channel=channel_id, ts=thread_ts, oldest=last_ts)
        return thread_messages['messages']
    except SlackApiError as e:
        logger.error(f'Error fetching conversation replies: {e}')
        return []
