#
# pip install python-telegram-bot python-dotenv openai cachetools
import os, sys, time, json, requests, logging, re, threading
from logging.handlers import RotatingFileHandler
from pathlib import Path
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import constants
from openai import OpenAI
from openai import OpenAIError
from collections import defaultdict, OrderedDict
from cachetools import TTLCache

exec_directory = Path(__file__).resolve().parent
os.chdir(exec_directory)
load_dotenv()

# 设置你的Telegram Bot Token和OpenAI API密钥
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ALLOWED_GROUP_IDS = json.loads(os.getenv('ALLOWED_GROUP_IDS'))

# 初始化OpenAI客户端
client = OpenAI(base_url="https://api.openai.com/v1", api_key=OPENAI_API_KEY)

# 加密货币符号的正则表达式
CRYPTO_PATTERN = r'\b[A-Za-z]{2,5}\b'

# CoinGecko API URL
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"

# 初始化缓存：币种列表（TTL为1小时），价格数据（TTL为5分钟）
coins_cache = TTLCache(maxsize=1, ttl=3600)  # 1小时更新一次币种列表
price_cache = TTLCache(maxsize=100, ttl=300)  # 5分钟缓存价格数据

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
    "Who created you": "I am an AI assistant developed by chatgpt."
}

# 获取所有支持的加密货币列表
def fetch_coins_list():
    # response = requests.get(f"{COINGECKO_API_URL}/coins/list")
    response = requests.get(f"{COINGECKO_API_URL}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1")
    data = response.json()
    coins_cache['coins_list'] = {}
    #coins_cache['coins_list'] = {coin['id']: coin['symbol'] for coin in data}
    for coin in data:
        if coin['id'] not in ['batcat', 'bifrost-bridged-eth-bifrost', 'bridged-binance-peg-ethereum-opbnb', 'bifrost-bridged-bnb-bifrost', 'bridged-wrapped-ether-starkgate']:
            coins_cache['coins_list'][coin['id']] = coin['symbol']
    logger.info("Fetched and cached coins list")

def format_price(price, digits=5):
    if abs(price) >= 1:
        # 对于绝对值大于等于1的数，显示2位小数
        return f"{price:.2f}"
    else:
        # 对于绝对值小于1的数，保留第一个非零数字后的指定位数
        abs_price = abs(price)
        if abs_price == 0:
            return "0." + "0" * digits

        # 找到第一个非零数字的位置
        first_non_zero = 0
        while abs_price < 0.1:
            abs_price *= 10
            first_non_zero += 1

        # 构建格式字符串，多保留几位以确保精度
        format_string = f"{{:.{first_non_zero + digits + 5}f}}"
        formatted = format_string.format(abs(price))

        # 截取到指定位数
        decimal_part = formatted.split('.')[1]
        formatted = "0." + decimal_part[:first_non_zero + digits]

        # 去掉末尾的零，但保留小数点
        formatted = formatted.rstrip('0')
        if formatted.endswith('.'):
            formatted += '0'

        # 如果原数是负数，添加负号
        return "-" + formatted if price < 0 else formatted

def get_crypto_data(coin_id, symbol: str):
    try:
        if symbol in price_cache:
            logging.info(f"Cache hit for {symbol}")
            return price_cache[symbol]

        # 从 CoinGecko API 获取价格数据
        response = requests.get(f"{COINGECKO_API_URL}/coins/{coin_id}")
        data = response.json()

        if not data:
            return None

        logging.info(f"COINGECKO_DATA, price_change_24h: {data['market_data']['price_change_percentage_24h']}, current_price: {data['market_data']['current_price']['usd']}, high_24h: {data['market_data']['high_24h']['usd']}, low_24h: {data['market_data']['low_24h']['usd']}")
        price_change_24h = data['market_data']['price_change_percentage_24h']
        price_change_24h = f"+{price_change_24h:.2f}" if price_change_24h > 0 else f"{price_change_24h:.2f}"
        current_price = data['market_data']['current_price']['usd']
        current_price = current_price if current_price > 1 else format_price(current_price, 5)
        high_24h = data['market_data']['high_24h']['usd']
        high_24h = high_24h if high_24h > 1 else format_price(high_24h, 5)
        low_24h = data['market_data']['low_24h']['usd']
        low_24h = low_24h if low_24h > 1 else format_price(low_24h, 5)
        crypto_data = {
            'id': data['id'],
            'name': data['name'],
            'symbol': data['symbol'].upper(),
            'current_price': current_price,
            'price_change_24h': price_change_24h,
            'high_24h': high_24h,
            'low_24h': low_24h
        }
        price_cache[symbol] = crypto_data
        logging.info(f"Cache set for {symbol}")
        return crypto_data

    except Exception as e:
        logger.error(f"获取加密货币数据时出错: {e}")
        return None

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
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I am an AI chatbot. @ me in the group or reply to my message to chat with me, or you can input <coin_symbol> to get the coin price. For example: btc")

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

    # 确保币种列表在缓存中
    if 'coins_list' not in coins_cache:
        fetch_coins_list()

    logger.info(f"Received message: '{message}' from user ID: {user_id} in chat ID: {chat_id}, ChatType: {update.message.chat.type}")

    # 检查是否在群组是否被允许
    if not is_allowed_chat(chat_id):
        logger.info(f"Message from unauthorized group: {chat_id}")
        # await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I only work in special groups.")
        return

    # 查找消息中的加密货币符号
    coins_list = coins_cache['coins_list']
    coin_id, symbol = None, None
    if message.lower().strip() in coins_list:
        coin_id, symbol = message.lower().strip(), coins_list[message.lower().strip()]
    else:
        for cid, sym in coins_list.items():
            if sym == message.lower().strip():
                coin_id, symbol = cid, sym
                break

    if coin_id:
        crypto_data = get_crypto_data(coin_id, symbol)
        logger.info(f"crypto_data_format {crypto_data}")
        if crypto_data:
            change_text = "📈" if crypto_data['price_change_24h'][0] == '+'  else "📉"
            message = (
                f"*{crypto_data['symbol']}/USDT Spot Market Data*\n\n"
                f"💰Current Price: {crypto_data['current_price']} USDT\n"
                f"{change_text}24h Change: {crypto_data['price_change_24h']}%\n"
                f"⬆️24h High: {crypto_data['high_24h']} USDT\n"
                f"⬇️24h Low:  {crypto_data['low_24h']} USDT\n\n"
                f"Start trading on [binance](https://binance.com)🚀"
            )
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode=constants.ParseMode.MARKDOWN)
            return  # 如果找到并发送了加密货币数据，就不再继续处理

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

# 定期更新币种列表
def schedule_fetch_coins_list():
    while True:
        fetch_coins_list()
        # 每小时更新一次币种列表
        threading.Event().wait(3600)

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    bot = application.bot
    #logger.info(f"bot username: {bot.username()}")
    fetch_coins_list()

    application.add_handler(CommandHandler("start", start))
    # application.add_handler(CommandHandler("getchatid", get_chat_id))
    # application.add_handler(CommandHandler("price", price))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    application.add_error_handler(error_handler)

    threading.Thread(target=schedule_fetch_coins_list, daemon=True).start()

    logger.info("Bot started polling")
    application.run_polling()

if __name__ == '__main__':
    main()
