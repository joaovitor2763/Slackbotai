from decouple import config

SLACK_BOT_TOKEN = config('SLACK_BOT_TOKEN')
SLACK_APP_TOKEN = config('SLACK_APP_TOKEN')
SLACK_SIGNING_SECRET = config('SLACK_SIGNING_SECRET')

OPENAI_API_KEY = config('OPENAI_API_KEY')

OPENAI_API_CODE_INTERPRETER_NAME = 'Bitcoin data analysis'
OPENAI_API_CODE_INTERPRETER_INSTRUCTIONS = 'You are a financial market data scientist. Write and answer bitcoins questions.'
OPENAI_API_CODE_INTERPRETER_THREAD_CONTENT = 'Analyze the data and give me a summary answer in text only'
