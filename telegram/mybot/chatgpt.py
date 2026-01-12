from openai import OpenAI, OpenAIError
from config import OPENAI_API_KEY
from logging_config import get_logger

# Initialize OpenAI API
client = OpenAI(base_url="https://api.openai.com/v1", api_key=OPENAI_API_KEY)

# Set up logging
logger = get_logger(__name__)

def get_chatgpt_response(user_message):
    # logger.info(f"User requested ChatGPT response: {user_message}")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content
    except OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        return "Sorry, I can't respond right now. Please try again later."
    except Exception as e:
        logger.exception(f"Unexpected error call ChatGpt: {e}")
        return "An unexpected error occurred, please try again later."
