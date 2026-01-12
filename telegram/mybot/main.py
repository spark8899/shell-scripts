import time, threading
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import constants
from collections import defaultdict, OrderedDict

from config import TELEGRAM_BOT_TOKEN, ALLOWED_GROUP_IDS, CUSTOM_QA
from tools import is_allowed_chat, rate_limit, get_cached_response, cache_response
from logging_config import setup_logging, get_logger
from crypto import fetch_coins_list, query_crypt_price
from chatgpt import get_chatgpt_response
from guess import post_guess

# Set up logging
setup_logging()
logger = get_logger(__name__)

async def help(update, context):
    logger.info(f"ALLOWED_GROUP_IDS: `{ALLOWED_GROUP_IDS}`, ChatID: `{update.effective_chat.id}`")
    if not is_allowed_chat(update.effective_chat.id):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I only work in special groups.")
        return
    text = "Hello! I am an AI chatbot. @ me in the group or reply to my message to chat with me, or you can input <coin_symbol> to get the coin price. For example: btc"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def price(update, context):
    chat_id, user_id = update.effective_chat.id, update.effective_user.id
    user_name = update.message.from_user.username or update.message.from_user.user.first_name or "UnknownUser"
    user_message = update.message.text

    if not is_allowed_chat(chat_id):
        return
    logger.info(f"Recive_price_Message: `{user_message}`, from_id: `{user_id}`, from_user: `{user_name}`")

    if len(context.args) == 0:
        await update.message.reply_text("Please provide a currency, e.g., /price btc")
        return

    code = user_message.split(' ')[-1].lower().strip()
    reply = query_crypt_price(code)
    if len(reply) > 0:
        await update.message.reply_text(reply, parse_mode=constants.ParseMode.MARKDOWN)

async def guess(update, context):
    chat_id, user_id = update.effective_chat.id, update.effective_user.id
    user_name = update.message.from_user.username or update.message.from_user.user.first_name or "UnknownUser"
    user_message = update.message.text
    logger.info(f"Recive_guess_Message: `{user_message}`, from_id: `{user_id}`, from_user: `{user_name}`")

    if not is_allowed_chat(chat_id):
        return

    # Check if content is provided
    if len(context.args) < 1:
        await update.message.reply_text("Please use the /guess <content> command to enter your guess.")
        return

    # Extract the guess content from the command arguments
    guess_content = ' '.join(context.args)  # Join all arguments to form the content

    info = post_guess(user_id, user_name, guess_content)
    await update.message.reply_text(info)


async def chat(update, context):
    chat_id, user_id = update.effective_chat.id, update.effective_user.id
    user_name = update.message.from_user.username or update.message.from_user.user.first_name or "UnknownUser"
    user_message = update.message.text
    bot_username = context.bot.username
    logger.info(f"Recive_chat_Message: `{user_message}`, from_id: `{user_id}`, from_user: `{user_name}`")

    if not is_allowed_chat(chat_id):
        return

    reply = query_crypt_price(user_message.lower().strip())
    if len(reply) > 0:
        logger.info(f"replay_crypt_price: `{user_message.lower().strip()}`")
        await update.message.reply_text(reply, parse_mode=constants.ParseMode.MARKDOWN)

    # Check if you have been @mentioned or replied to in the group
    if update.message.chat.type != 'private':
        if not (update.message.text.startswith(f'@{bot_username}') or (update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id)):
            logger.debug("Not mentioned or replied to")
            return

    if not rate_limit(user_id):
        logger.warning(f"Rate limit exceeded for user ID: `{user_id}`, Name: `{user_name}`")
        await update.message.reply_text("The request was too frequent. Please try again later.")
        return

    if user_message.startswith(f'@{bot_username}'):
        user_message = user_message[len(f'@{bot_username}'):].strip()

    logger.info(f"Processed_ai_message: `{user_message}`")

    # Check if it is a customization issue
    if user_message in CUSTOM_QA:
        response = CUSTOM_QA[user_message]
        logger.info(f"HIT Custom_QA response for chat")
    else:
        # Check the cache
        cached_response = get_cached_response(user_message)
        if cached_response:
            response = cached_response
            logger.info(f"HIT Cache response for chat")
        else:
            response = get_chatgpt_response(user_message)
            cache_response(user_message, response)
            logger.info("New response generated and cached")

    logger.info(f"Response_ai: `{response}`")
    await update.message.reply_text(response)

async def error_handler(update, context):
    logger.info(f"Exception while handling an update: {context.error}")

# Regularly updated cryptocurrency list
def schedule_fetch_coins_list():
    while True:
        fetch_coins_list()
        # The list is updated every hour
        threading.Event().wait(3600)

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    bot = application.bot

    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("price", price))
    application.add_handler(CommandHandler("guess", guess))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    application.add_error_handler(error_handler)

    threading.Thread(target=schedule_fetch_coins_list, daemon=True).start()

    logger.info("Bot started polling")
    application.run_polling()

if __name__ == '__main__':
    main()
