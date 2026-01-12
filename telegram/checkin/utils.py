import random
import string
import logging
from db_operations import execute_query, execute_insert
from config import CHAT_ID, LOG_LEVEL, LOG_FILE
import datetime

def setup_logger(name):
    """Set up and return a logger"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL.upper()))

    # Create file handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(getattr(logging, LOG_LEVEL.upper()))

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL.upper()))

    # Create formatter with filename and line number
    formatter = logging.Formatter('%(asctime)s - %(filename)s:%(lineno)d - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def get_or_create_invite_code(user_id):
    result = execute_query("SELECT invite_code FROM invites WHERE inviter_id = %s", (user_id,))
    if result:
        invite_code = result[0][0]
    else:
        invite_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        execute_insert("INSERT INTO invites (inviter_id, invite_code) VALUES (%s, %s)", (user_id, invite_code))
    return invite_code

def get_weekly_checkins(user_id):
    one_week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    result = execute_query("""
        SELECT COUNT(*) FROM checkins
        WHERE user_id = %s AND checkin_time > %s
    """, (user_id, one_week_ago))
    return result[0][0]

def send_daily_leaderboard(context):
    result = execute_query("""
        SELECT username, points
        FROM points
        ORDER BY points DESC
        LIMIT 10
    """)

    if result:
        leaderboard = "Daily Points Leaderboard:\n"
        for i, (username, points) in enumerate(result, 1):
            leaderboard += f"{i}. @{username}: {points} points\n"
    else:
        leaderboard = "No points recorded yet."

    context.bot.send_message(chat_id=CHAT_ID, text=leaderboard)
    logger.info("Daily leaderboard sent.")
