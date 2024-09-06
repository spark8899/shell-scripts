#
# pip install python-telegram-bot python-dotenv openai
import os, sys, time, json, requests, logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from openai import OpenAI
from openai import OpenAIError
from collections import defaultdict, OrderedDict

exec_directory = Path(__file__).resolve().parent
os.chdir(exec_directory)
load_dotenv()

# 设置你的Telegram Bot Token和OpenAI API密钥
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ALLOWED_GROUP_IDS = json.loads(os.getenv('ALLOWED_GROUP_IDS'))

# 初始化OpenAI客户端
client = OpenAI(base_url="https://apis.wumingai.com/v1", api_key=OPENAI_API_KEY)

# 配置日志
def setup_logger():
    logger = logging.getLogger('bot_logger')
    logger.setLevel(logging.DEBUG)

    # 创建一个按大小轮询的文件处理器
    file_handler = RotatingFileHandler(
        'bot.log',
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)

    # 创建一个格式器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # 将处理器添加到日志记录器
    logger.addHandler(file_handler)

    return logger

# 创建日志记录器
logger = setup_logger()

# 用户请求频率限制
USER_RATE_LIMIT = 5  # 每个用户每分钟的最大请求次数
user_request_times = defaultdict(list)

# 简单的缓存实现
CACHE_SIZE = 100
cache = OrderedDict()

# 自定义问题和回答
custom_qa = {
    "who are you": "I am an AI assistant powered by OpenAI's GPT model.",
    "What you can do": "I can answer questions, provide information, engage in simple conversation, etc. Is there anything I can help you with?",
    "Who created you": "I am an AI assistant developed by chatGPT."
}

def is_allowed_chat(chat_id):
    return chat_id in ALLOWED_GROUP_IDS

def rate_limit(user_id):
    current_time = time.time()
    user_request_times[user_id] = [t for t in user_request_times[user_id] if current_time - t < 60]
    user_request_times[user_id].append(current_time)
    return len(user_request_times[user_id]) <= USER_RATE_LIMIT

def get_cached_response(message):
    return cache.get(message)

def cache_response(message, response):
    cache[message] = response
    if len(cache) > CACHE_SIZE:
        cache.popitem(last=False)

async def start(update, context):
    logger.info(f"ALLOWED_GROUP_IDS: {ALLOWED_GROUP_IDS}")
    logger.info(f"chatID: {update.effective_chat.id}")
    if not is_allowed_chat(update.effective_chat.id):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I only work in special groups.")
        return
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I am an AI chatbot. @ me in the group or reply to my message to chat with me, or you can use /price <coin_symbol> to get the coin price. For example: /price btc")

async def price(update, context):
    chat_id = update.effective_chat.id
    if not is_allowed_chat(chat_id):
        logger.info(f"Message from unauthorized group: {chat_id}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I only work in special groups.")
        return
    try:
        # 获取用户输入的加密货币代码
        _, symbol = update.message.text.split(maxsplit=1)
        symbol = symbol.upper().strip()

        # 使用CoinGecko API获取价格
        url = f"https://api.coingecko.com/api/v3/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 250,
            'page': 1,
            'sparkline': False
        }
        response = requests.get(url, params=params)
        data = response.json()

        # 查找匹配的加密货币
        coin = next((item for item in data if item['symbol'].upper() == symbol), None)

        if coin:
            name = coin['name']
            current_price = coin['current_price']
            market_cap = coin['market_cap']
            price_change_24h = coin['price_change_percentage_24h']

            reply = f"{name} ({symbol}) current price: \n"
            reply += f"💰 ${current_price:.2f} USD\n"
            reply += f"📊 24H changes: {price_change_24h:.2f}%\n"
            reply += f"💼 Market Cap: ${market_cap:,.0f} USD"

            await context.bot.send_message(chat_id=update.effective_chat.id, text=reply, reply_to_message_id=update.message.message_id)
        else:
            response = f"Cryptocurrency with code {symbol} not found, please check that you have entered it correctly."
            await context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_to_message_id=update.message.message_id)
    except ValueError:
        response = "Please specify a cryptocurrency symbol (e.g., /price btc)."
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_to_message_id=update.message.message_id)
    except Exception as e:
        response = f"An error occurred: {str(e)}"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_to_message_id=update.message.message_id)

async def chat(update, context):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    message = update.message.text
    bot_username = context.bot.username

    logger.info(f"Received message: '{message}' from user ID: {user_id} in chat ID: {chat_id}, ChatType: {update.message.chat.type}")

    # 检查是否在群组是否被允许
    if not is_allowed_chat(chat_id):
        logger.info(f"Message from unauthorized group: {chat_id}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I only work in special groups.")
        return

    # 检查是否在群组中被@提及或回复
    if update.message.chat.type != 'private':
        if not (update.message.text.startswith(f'@{bot_username}') or (update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id)):
            logging.debug("Not mentioned or replied to")
            return

    if not rate_limit(user_id):
        logger.warning(f"Rate limit exceeded for user ID: {user_id}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="The request was too frequent. Please try again later.", reply_to_message_id=update.message.message_id)
        return

    # 去掉@username部分（如果有的话）
    if message.startswith(f'@{bot_username}'):
        message = message[len(f'@{bot_username}'):].strip()

    logger.info(f"Processed message: {message}")

    # 检查是否是自定义问题
    if message in custom_qa:
        response = custom_qa[message]
        logger.info(f"Custom response for message: '{message}'")
    else:
        # 检查缓存
        cached_response = get_cached_response(message)
        if cached_response:
            response = cached_response
            logger.info("Response retrieved from cache")
        else:
            response = get_ai_response(message)
            cache_response(message, response)
            logger.info("New response generated and cached")

    logger.info(f"Response: {response}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_to_message_id=update.message.message_id)

def get_ai_response(message):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        return "Sorry, I can't respond right now. Please try again later."
    except Exception as e:
        logger.exception(f"Unexpected error in get_ai_response: {e}")
        return "An unexpected error occurred, please try again later."

async def get_chat_id(update, context):
    chat_id = update.effective_chat.id
    logger.info(f"Get chat ID command received. Chat ID: {chat_id}")
    await context.bot.send_message(chat_id=chat_id, text=f"This chat's ID is: {chat_id}")

async def error_handler(update, context):
    logging.info(f"Exception while handling an update: {context.error}")

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    # application.add_handler(CommandHandler("getchatid", get_chat_id))
    application.add_handler(CommandHandler("price", price))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    application.add_error_handler(error_handler)

    logger.info("Bot started polling")
    application.run_polling()

if __name__ == '__main__':
    main()
