## pip install tweepy python-telegram-bot python-dotenv
import tweepy
import telegram
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Twitter API 凭证
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

# Telegram Bot Token 和群组 ID
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# 设置 Twitter API
auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
twitter_api = tweepy.API(auth)

# 设置 Telegram Bot
telegram_bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

# 定义要监听的 Twitter 用户
TWITTER_USER = 'example_user'

class MyStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        # 获取推文文本
        tweet_text = status.text
        
        # 构建推文链接
        tweet_link = f"https://twitter.com/{status.user.screen_name}/status/{status.id}"
        
        # 组合消息
        message = f"New tweet from {status.user.name} (@{status.user.screen_name}):\n\n{tweet_text}\n\n{tweet_link}"
        
        # 发送到 Telegram
        telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

# 创建并启动 Twitter 流
myStreamListener = MyStreamListener()
myStream = tweepy.Stream(auth = twitter_api.auth, listener=myStreamListener)
myStream.filter(follow=[twitter_api.get_user(screen_name=TWITTER_USER).id_str])
