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
    BotCommand("price", "Get cryptocurrency prices (For example: /price bitcoin)")
]

# setting bot command
bot.set_my_commands(commands)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Use /price <coin> to get the current price of a cryptocurrency. For example: /price bitcoin")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = 'Use /price <coin> to get the current price of a cryptocurrency. For example: /price bitcoin'
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['price'])
def get_crypto_price(message):
    try:
        # 获取用户输入的加密货币代码
        _, coin = message.text.split(maxsplit=1)
        coin = coin.lower().strip()

        # 使用CoinGecko API获取价格
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()

        if coin in data:
            price = data[coin]['usd']
            bot.reply_to(message, f"The current price of {coin} is ${price:.2f} USD.")
        else:
            bot.reply_to(message, f"Could not retrieve price for '{coin}'. Please check the symbol and try again.")
    except ValueError:
        bot.reply_to(message, "Please specify a cryptocurrency symbol (e.g., /price bitcoin).")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {str(e)}")

@bot.message_handler(func=lambda message: message.text.startswith('/'))
def handle_unknown_command(message):
    bot.reply_to(message, "Unknown command. Please use /help to get available commands")

# start bot.
bot.polling()
