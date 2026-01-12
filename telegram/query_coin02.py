#
# pip install pyTelegramBotAPI requests dotenv
import telebot
from telebot.types import BotCommand
import requests
import logging, asyncio, os, sys
from pathlib import Path
from dotenv import load_dotenv

exec_directory = Path(__file__).resolve().parent
os.chdir(exec_directory)
load_dotenv()

# Telegram config
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# setting logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# setting command list
commands = [
    BotCommand("start", "Getting started with the robot."),
    BotCommand("help", "Get help information."),
    BotCommand("price", "Get cryptocurrency prices (For example: /price btc)")
]

# setting bot command
bot.set_my_commands(commands)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Use /price <coin> to get the current price of a cryptocurrency. For example: /price btc")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = 'Use /price <coin> to get the current price of a cryptocurrency. For example: /price btc'
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['price'])
def get_crypto_price(message):
    try:
        # 获取用户输入的加密货币代码
        _, symbol = message.text.split(maxsplit=1)
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

            bot.reply_to(message, reply)
        else:
            bot.reply_to(message, f"Cryptocurrency with code {symbol} not found, please check that you have entered it correctly.")
    except ValueError:
        bot.reply_to(message, "Please specify a cryptocurrency symbol (e.g., /price btc).")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {str(e)}")

@bot.message_handler(func=lambda message: message.text.startswith('/'))
def handle_unknown_command(message):
    bot.reply_to(message, "Unknown command. Please use /help to get available commands")

# start bot.
bot.polling()
