#
# install python3.10
# pip install twscrape python-telegram-bot pyyaml python-dotenv
# */15 * * * * /root/twToTel/venv/bin/python3.10 /root/twToTel/fow01.py > /root/twToTel/1.log 2>&1
import os, sys, time, yaml, telegram, asyncio, twscrape
from pathlib import Path
from dotenv import load_dotenv

exec_directory = Path(__file__).resolve().parent
os.chdir(exec_directory)
load_dotenv()

# Telegram config
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
ALERT_TELEGRAM_BOT_TOKEN = os.getenv('ALERT_TELEGRAM_BOT_TOKEN')
ALERT_TELEGRAM_CHAT_ID = os.getenv('ALERT_TELEGRAM_CHAT_ID')

# monitor Twitter user_id
TWITTER_USER_ID = os.getenv('TWITTER_USER_ID_TO_MONITOR')

# init Telegram Bot
telegram_bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
now = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time()))

# setting config
filename = Path(exec_directory, 'config.yaml')

def read_yaml(filename):
    with open(filename, 'r') as file:
        return yaml.safe_load(file)

def write_yaml(filename, data):
    with open(filename, 'w') as file:
        yaml.dump(data, file, default_flow_style=False)

def get_value(filename, key):
    data = read_yaml(filename)
    return data.get(key)

def set_value(filename, key, value):
    data = read_yaml(filename)
    data[key] = value
    write_yaml(filename, data)

async def worker(api: twscrape.API, uid: str):
    tweets = []
    try:
        tss = await twscrape.gather(api.user_tweets(uid, limit=10))
        for i in tss:
            tw = {"id": i.id_str, "datetime": i.date.strftime('%Y-%m-%d %H:%M:%S'),
                "conversationId": i.conversationIdStr, "inReplyToTweetId": i.inReplyToTweetIdStr,
                "url": i.url, "rawContent": i.rawContent, "media": i.media.dict()}
            tweets.append(tw)
        tweets.sort(key=lambda x: x['datetime'], reverse=True)
    except Exception as e:
        print(e)
    finally:
        return tweets

async def main():
    api = twscrape.API()
    tweets = []
    stats = await asyncio.gather(api.pool.stats())
    if stats[0]['active'] <= 0:
        alert_telegram_bot = telegram.Bot(token=ALERT_TELEGRAM_BOT_TOKEN)
        alert_message = f"account error: total: {stats[0]['total']}, acitve: {stats[0]['active']}"
        print(alert_message)
        await alert_telegram_bot.send_message(chat_id=ALERT_TELEGRAM_CHAT_ID, text=alert_message)
        sys.exit(120)
    results = await asyncio.gather(worker(api, TWITTER_USER_ID))
    old_id = get_value(filename, 'forwardID')
    for i in results[0]:
        if i['id'] == old_id:
            break
        else:
            if i['conversationId'] == i['id']:
                tweets.append(i)
    tweets.reverse()
    for i in tweets:
        rawContent = i['rawContent']
        if rawContent.split('\n')[-1].find('#') != -1:
            rawContent = '\n'.join(rawContent.split('\n')[:-1])
        elif len(rawContent.split('\n')) > 1 and rawContent.split('\n')[-2].find('#') != -1:
            last_line = rawContent.split('\n')[-1]
            mt = rawContent.split('\n')[:-2]
            mt.append(last_line)
            rawContent = '\n'.join(mt)
        elif  len(rawContent.split('\n')) > 2 and rawContent.split('\n')[-3].find('#') != -1:
            last_line = rawContent.split('\n')[-1]
            last_two_line = rawContent.split('\n')[-2]
            mt = rawContent.split('\n')[:-3]
            mt.append(last_two_line)
            mt.append(last_line)
            rawContent = '\n'.join(mt)
        message = f"{rawContent}\n"
        message = message.replace("#", "").replace("_", " ")
        for x in i['media']['photos']:
            message = f"{message}[ ]({x['url']})"
        for x in i['media']['videos']:
            message = f"{message}[ ]({x['variants'][0]['url']})"
        message = f"{message}\n👉 Quote address: {i['url']}"
        print(message)
        await telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode=telegram.constants.ParseMode.MARKDOWN)
        await telegram_bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message, parse_mode=telegram.constants.ParseMode.MARKDOWN)
        print(i['id'])
    if old_id != results[0][0]['id']:
        set_value(filename, 'forwardID', results[0][0]['id'])
    if now[11:15] == "00:0":
        alert_telegram_bot = telegram.Bot(token=ALERT_TELEGRAM_BOT_TOKEN)
        alert_message = f"forwardID: {results[0][0]['id']}"
        await alert_telegram_bot.send_message(chat_id=ALERT_TELEGRAM_CHAT_ID, text=alert_message)

if __name__ == "__main__":
    asyncio.run(main())
    print("all done.")
