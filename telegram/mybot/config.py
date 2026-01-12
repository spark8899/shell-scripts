import os, json
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ALLOWED_GROUP_IDS = json.loads(os.getenv('ALLOWED_GROUP_IDS'))

# Create a connection pool
DBCONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE")
}

# custom qa
CUSTOM_QA = {
    "who are you": "I am an AI assistant powered by AI",
    "What you can do": "I can answer questions, provide information, engage in simple conversation, etc. Is there anything I can help you with?",
    "Who created you": "I am an AI assistant developed by AI."
}
