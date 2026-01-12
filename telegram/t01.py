#
# python3 -m venv venv
# pip3 install python-telegram-bot pillow schedule

import logging
import schedule
import time
import asyncio
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from telegram import Bot

# 设置日志
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# 您的Bot API令牌
TOKEN = 'YOUR_TELEGRAM_BOT_API_TOKEN'

# 群组的chat_id
CHAT_ID = 'YOUR_CHAT_ID'

# 倒计时的目标日期
TARGET_DATE = datetime(2024, 12, 31)

# 图标的文件路径
ICON_PATH = 'icon.png'

# 背景图片的路径
BACKGROUND_PATH = 'background.png'

def generate_countdown_image():
    """生成带有日期倒计时的图片"""
    now = datetime.now()
    countdown = TARGET_DATE - now
    days_left = countdown.days

    # 创建空白图像
    #img = Image.new('RGB', (500, 500), color=(73, 109, 137))
    img = Image.open(BACKGROUND_PATH)
    draw = ImageDraw.Draw(img)

    # 设置字体
    font = ImageFont.truetype("msyh.ttf", 100)

    # 绘制文本
    text = f'剩余 {days_left} 天'
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    # position = ((img.width - text_width) / 2, (img.height - text_height) / 2)  # 中间
    # position = ((img.width - text_width) / 2, img.height - text_height -20 ) # 放在底部中心
    position = (img.width - text_width - 20, img.height - text_height - 50 ) # 放在右下角
    draw.text(position, text, font=font, fill=(0, 0, 255)) # 使用蓝色填充 (R, G, B)

    # 保存图像
    img.save(ICON_PATH)

async def change_group_icon():
    """更改群组图标"""
    bot = Bot(TOKEN)
    try:
        generate_countdown_image()
        with open(ICON_PATH, 'rb') as icon_file:
            await bot.set_chat_photo(chat_id=CHAT_ID, photo=icon_file)
        logger.info('Group icon changed successfully!')
    except Exception as e:
        logger.error(f'Error: {e}')

def main():
    """运行定时任务"""
    schedule.every().day.at("00:00").do(lambda: asyncio.run(change_group_icon()))

    # 立即运行一次任务
    asyncio.run(change_group_icon())

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
