#!/usr/bin/env python
"""slack openai  chat bot"""

import logging

from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt import App

from src.settings import SLACK_APP_TOKEN, SLACK_BOT_TOKEN
from src import slack_events


conversation_threads = {}
last_processed_message_ts = {}

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

app = App(token=SLACK_BOT_TOKEN)


@app.event('app_mention')
def handle_mention(body, say):
    slack_events.handle_mention(body, say, app, conversation_threads, last_processed_message_ts)


@app.event('message')
def handle_message_events(body, logger):
    logger.info('Received message: %s', body)


def main():
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()


if __name__ == '__main__':
    main()
