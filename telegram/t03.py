import logging
import schedule
import time
import asyncio
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode

# 设置日志
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# 您的Bot API令牌
TOKEN = 'YOUR_TELEGRAM_BOT_API_TOKEN'

# 群组的chat_id
CHAT_ID = 'YOUR_CHAT_ID'

# 倒计时的目标日期
TARGET_DATE = datetime(2024, 12, 31)

# 记录当前和前一天的消息ID
pinned_message_id = None

async def send_countdown_message():
    global pinned_message_id
    """发送倒计时消息并置顶"""
    bot = Bot(TOKEN)
    try:
        now = datetime.now()
        countdown = TARGET_DATE - now
        days_left = countdown.days
        test = f"距离目标日期还有 {days_left} 天！"

        # 发送消息并获取消息ID
        message = await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode=ParseMode.HTML)

        # 置顶消息
        await bot.pin_chat_message(chat_id=CHAT_ID, message_id=message.message_id, disable_notification=True)

        # 删除前一天的置顶消息
        if pinned_message_id:
            try:
                await bot.delete_message(chat_id=CHAT_ID, message_id=pinned_message_id)
                logger.info(f'Previous pinned message {pinned_message_id} deleted successfully!')
            except Exception as e:
                logger.error(f'Error deleting previous message {pinned_message_id}: {e}')

        # 更新前一天的消息ID为当前消息ID
        pinned_message_id = message.message_id

        logger.info(f'Countdown message {pinned_message_id} sent and pinned successfully!')
    except Exception as e:
        logger.error(f'Error: {e}')

def run_schedule():
    """运行定时任务"""
    schedule.every().day.at("00:00").do(lambda: asyncio.run(send_countdown_message()))

    # 立即运行一次任务
    asyncio.run(send_countdown_message())

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    run_schedule()
