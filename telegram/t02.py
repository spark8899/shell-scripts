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

def round_rectangle(draw, xy, radius, fill=None, outline=None):
    """绘制圆角矩形"""
    x0, y0, x1, y1 = xy
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill, outline=outline)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill, outline=outline)
    draw.pieslice([x0, y0, x0 + 2*radius, y0 + 2*radius], 180, 270, fill=fill, outline=outline)
    draw.pieslice([x1 - 2*radius, y0, x1, y0 + 2*radius], 270, 360, fill=fill, outline=outline)
    draw.pieslice([x0, y1 - 2*radius, x0 + 2*radius, y1], 90, 180, fill=fill, outline=outline)
    draw.pieslice([x1 - 2*radius, y1 - 2*radius, x1, y1], 0, 90, fill=fill, outline=outline)

def generate_countdown_image():
    """生成带有日期倒计时的图片"""
    now = datetime.now()
    countdown = TARGET_DATE - now
    days_left = countdown.days

    # 打开背景图像
    img = Image.open(BACKGROUND_PATH)
    draw = ImageDraw.Draw(img)

    # 设置字体（中文）
    font_path = "SimHei.ttf"  # 替换为中文字体文件的路径
    font = ImageFont.truetype(font_path, 100)

    # 计算文本大小和位置
    text = f'剩余 {days_left} 天'
    text_width, text_height = draw.textsize(text, font=font)
    padding = 20
    radius = 30
    box_width = text_width + 2 * padding
    box_height = text_height + 2 * padding
    position = (img.width - box_width - 20, img.height - box_height - 50)  # 调整此值上移文本

    # 绘制圆角矩形背景（灰色）
    round_rectangle(draw, [position[0], position[1], position[0] + box_width, position[1] + box_height], radius, fill=(192, 192, 192, 128))

    # 绘制文本（蓝色）
    text_position = (position[0] + padding, position[1] + padding)
    draw.text(text_position, text, font=font, fill=(0, 0, 255))  # 使用蓝色填充 (R, G, B)

    # 保存图像
    img.save(ICON_PATH)

async def change_group_icon():
    """更改群组图标"""
    bot = Bot(TOKEN)
    try:
        generate_countdown_image()
        with open(ICON_PATH, 'rb') as icon_file:
            await bot.set_chat_photo(chat_id=CHAT_ID, photo=icon_file)  # 等待这里完成
        logger.info('Group icon changed successfully!')
    except Exception as e:
        logger.error(f'Error: {e}')

def run_schedule():
    """运行定时任务"""
    schedule.every().day.at("00:00").do(lambda: asyncio.run(change_group_icon()))

    # 立即运行一次任务
    asyncio.run(change_group_icon())

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    run_schedule()
