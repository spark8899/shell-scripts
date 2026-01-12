from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from db_operations import execute_query, execute_insert
from utils import get_or_create_invite_code, get_weekly_checkins, setup_logger
from config import GROUP_INVITE_LINK, CHAT_ID
import datetime
import urllib.parse

logger = setup_logger(__name__)

def start(update: Update, context: CallbackContext):
    full_command = update.message.text
    logger.info(f"Start command received. Full message: {full_command}")
    if ' ' in full_command:
        _, invite_code = full_command.split(' ', 1)
        logger.info(f"Invite code received: {invite_code}")
        user_id = update.effective_user.id

        result = execute_query("SELECT * FROM processed_invites WHERE user_id=%s AND invite_code=%s", (user_id, invite_code))
        if result:
            update.message.reply_text("You have already used this invite link.")
            return

        result = execute_query("SELECT inviter_id FROM invites WHERE invite_code = %s", (invite_code,))
        if result:
            inviter_id = result[0][0]

            callback_data = f"join_{invite_code}_{user_id}"

            keyboard = [[InlineKeyboardButton("Join Group", url=GROUP_INVITE_LINK, callback_data=callback_data)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            update.message.reply_text("Welcome! Click the button below to join the group:", reply_markup=reply_markup)

            execute_insert("INSERT INTO processed_invites (user_id, invite_code, processed_time) VALUES (%s, %s, %s)",
                      (user_id, invite_code, datetime.datetime.now()))
        else:
            update.message.reply_text("Invalid invite code.")
    else:
        send_welcome(update, context)

def checkin(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.effective_user.username
    now = datetime.datetime.now()
    today = now.date()

    result = execute_query("SELECT * FROM checkins WHERE user_id=%s AND DATE(checkin_time)=%s", (user_id, today))
    if result:
        update.message.reply_text("You've already checked in today. Come back tomorrow!")
        logger.info(f"User {username} (ID: {user_id}) attempted to check in again.")
    else:
        execute_insert("INSERT INTO checkins (user_id, username, checkin_time) VALUES (%s, %s, %s)", (user_id, username, now))
        execute_query("INSERT INTO points (user_id, username, points) VALUES (%s, %s, 1) ON DUPLICATE KEY UPDATE points = points + 1", (user_id, username))

        result = execute_query("SELECT streak_days, last_checkin FROM streak WHERE user_id=%s", (user_id,))
        if result:
            streak_days, last_checkin = result[0]
            if (today - last_checkin).days == 1:
                streak_days += 1
            elif (today - last_checkin).days > 1:
                streak_days = 1
        else:
            streak_days = 1

        execute_query("INSERT INTO streak (user_id, username, streak_days, last_checkin) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE streak_days = %s, last_checkin = %s",
                       (user_id, username, streak_days, today, streak_days, today))

        weekly_checkins = get_weekly_checkins(user_id)
        eligible = weekly_checkins >= 5

        execute_query("""
            INSERT INTO lottery_eligibility (user_id, username, eligible, last_eligible_date, weekly_streak)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            eligible = %s, last_eligible_date = %s, weekly_streak = %s
        """, (user_id, username, eligible, today, weekly_checkins, eligible, today, weekly_checkins))

        reply_message = f"Check-in successful! Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}\nYou've earned 1 point!\nYour current streak: {streak_days} days"

        if eligible:
            reply_message += "\nCongratulations! You're eligible for the next lottery draw!"
        else:
            reply_message += f"\nYou need {5 - weekly_checkins} more check-ins this week to be eligible for the lottery draw!"

        update.message.reply_text(reply_message)
        logger.info(f"User {username} (ID: {user_id}) checked in successfully. Streak: {streak_days} days, Weekly check-ins: {weekly_checkins}.")

def show_points(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    result = execute_query("SELECT points FROM points WHERE user_id=%s", (user_id,))

    if result:
        points = result[0][0]
        update.message.reply_text(f"Your current points: {points}")
        logger.info(f"User {update.effective_user.username} (ID: {user_id}) checked their points: {points}")
    else:
        execute_insert("INSERT INTO points (user_id, username, points) VALUES (%s, %s, 0)", (user_id, update.effective_user.username))
        update.message.reply_text("You don't have any points yet. Check in or invite friends to start earning!")
        logger.info(f"User {update.effective_user.username} (ID: {user_id}) checked their points but had none. Created a new record.")

def show_leaderboard(update: Update, context: CallbackContext):
    result = execute_query("""
        SELECT username, points
        FROM points
        ORDER BY points DESC
        LIMIT 10
    """)

    if result:
        leaderboard = "Points Leaderboard:\n"
        for i, (username, points) in enumerate(result, 1):
            leaderboard += f"{i}. @{username}: {points} points\n"
    else:
        leaderboard = "No points recorded yet."

    update.message.reply_text(leaderboard)
    logger.info(f"User {update.effective_user.username} (ID: {update.effective_user.id}) requested the leaderboard.")

def invite(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    invite_code = get_or_create_invite_code(user_id)

    encoded_invite_code = urllib.parse.quote(invite_code)
    invite_link = f"https://t.me/{context.bot.username}?start={encoded_invite_code}"

    keyboard = [[InlineKeyboardButton("Share Invite Link", url=invite_link)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(f"Here's your invite link: {invite_link}\nShare this link with your friends. When they join the group using this link, you'll earn 15 points!", reply_markup=reply_markup)
    logger.info(f"User {update.effective_user.username} (ID: {user_id}) requested their invite link.")

def show_my_invites(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    result = execute_query("""
        SELECT invite_code, uses
        FROM invites
        WHERE inviter_id = %s
    """, (user_id,))

    if result:
        invite_code, uses = result[0]
        invite_link = f"https://t.me/{context.bot.username}?start={invite_code}"
        invite_info = f"Your invite link: {invite_link}\nNumber of uses: {uses}"
    else:
        invite_info = "You don't have an invite link yet. Use /invite to generate one."

    update.message.reply_text(invite_info)
    logger.info(f"User {update.effective_user.username} (ID: {user_id}) checked their invite information.")

def show_invite_leaderboard(update: Update, context: CallbackContext):
    result = execute_query("""
        SELECT p.username, i.uses
        FROM invites i
        JOIN points p ON i.inviter_id = p.user_id
        ORDER BY i.uses DESC
        LIMIT 10
    """)

    if result:
        leaderboard = "Invite Leaderboard:\n"
        for i, (username, uses) in enumerate(result, 1):
            leaderboard += f"{i}. @{username}: {uses} invites\n"
    else:
        leaderboard = "No invites recorded yet."

    update.message.reply_text(leaderboard)
    logger.info(f"User {update.effective_user.username} (ID: {update.effective_user.id}) requested the invite leaderboard.")

def lottery_status(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    result = execute_query("SELECT eligible, last_eligible_date FROM lottery_eligibility WHERE user_id=%s", (user_id,))

    weekly_checkins = get_weekly_checkins(user_id)

    if result:
        eligible, last_eligible_date = result[0]
        if eligible:
            status_message = f"You are eligible for the next lottery draw! You became eligible on {last_eligible_date}."
        else:
            status_message = f"You are not currently eligible for the lottery draw. You need {5 - weekly_checkins} more check-ins this week to become eligible!"
    else:
        status_message = f"You are not currently eligible for the lottery draw. You need {5 - weekly_checkins} more check-ins this week to become eligible!"

    update.message.reply_text(status_message)
    logger.info(f"User {update.effective_user.username} (ID: {user_id}) checked their lottery status.")

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data.startswith('join_'):
        _, invite_code, user_id = query.data.split('_')
        user_id = int(user_id)

        chat_member = context.bot.get_chat_member(CHAT_ID, user_id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            result = execute_query("SELECT inviter_id FROM invites WHERE invite_code = %s", (invite_code,))
            if result:
                inviter_id = result[0][0]
                execute_query("UPDATE points SET points = points + 15 WHERE user_id = %s", (inviter_id,))
                execute_query("UPDATE invites SET uses = uses + 1 WHERE invite_code = %s", (invite_code,))
                query.edit_message_text("You've successfully joined the group and the inviter has received points!")
                context.bot.send_message(inviter_id, f"User {query.from_user.username} has joined the group using your invite link. You've earned 15 points!")
            else:
                query.edit_message_text("Error processing invite. Please contact support.")
        else:
            query.edit_message_text("You need to join the group first!")

def send_welcome(update: Update, context: CallbackContext):
    welcome_text = (
        "Welcome to the Check-in Bot!\n\n"
        "Available commands:\n"
        "/checkin - Daily check-in (earn 1 point)\n"
        "/mypoints - View my points\n"
        "/leaderboard - View points leaderboard\n"
        "/invite - Get your invite link (earn 15 points per invite)\n"
        "/myinvites - View your invite information\n"
        "/inviteleaderboard - View invite leaderboard\n"
        "/lottery_status - Check your lottery eligibility status\n\n"
        f"The points leaderboard will be automatically posted every day at {LEADERBOARD_TIME}."
    )
    update.message.reply_text(welcome_text)
    logger.info(f"Welcome message sent to user {update.effective_user.username} (ID: {update.effective_user.id})")
