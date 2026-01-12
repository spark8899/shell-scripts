from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from config import BOT_TOKEN, LEADERBOARD_TIME
from commands import start, checkin, show_points, show_leaderboard, invite, show_my_invites, show_invite_leaderboard, lottery_status, button
from utils import send_daily_leaderboard, setup_logger
import datetime

logger = setup_logger(__name__)

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("checkin", checkin))
    dp.add_handler(CommandHandler("mypoints", show_points))
    dp.add_handler(CommandHandler("leaderboard", show_leaderboard))
    dp.add_handler(CommandHandler("invite", invite))
    dp.add_handler(CommandHandler("myinvites", show_my_invites))
    dp.add_handler(CommandHandler("inviteleaderboard", show_invite_leaderboard))
    dp.add_handler(CommandHandler("lottery_status", lottery_status))
    dp.add_handler(CallbackQueryHandler(button))

    job_queue = updater.job_queue
    job_queue.run_daily(send_daily_leaderboard,
                        datetime.time(hour=int(LEADERBOARD_TIME.split(':')[0]),
                                      minute=int(LEADERBOARD_TIME.split(':')[1])))

    logger.info("Bot started polling.")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    logger.info("Bot script started.")
    main()
