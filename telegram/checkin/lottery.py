from utils import setup_logger
from db_operations import execute_query, execute_insert
import random

logger = setup_logger(__name__)

def run_lottery():
    try:
        # Get all eligible users
        eligible_users = execute_query("SELECT user_id, username FROM lottery_eligibility WHERE eligible = TRUE")

        if len(eligible_users) < 10:
            logger.warning("Not enough eligible users for the lottery.")
            return

        # Randomly select 10 winners
        winners = random.sample(eligible_users, 10)

        logger.info("Lottery Winners:")
        for i, (user_id, username) in enumerate(winners, 1):
            logger.info(f"{i}. @{username} (ID: {user_id})")

        # Reset eligibility for all users
        execute_query("UPDATE lottery_eligibility SET eligible = FALSE")

        # Add points to winners (for example, 100 points each)
        for user_id, _ in winners:
            execute_query("UPDATE points SET points = points + 100 WHERE user_id = %s", (user_id,))

        logger.info("Lottery completed successfully.")

    except Exception as e:
        logger.error(f"An error occurred during the lottery: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting lottery script.")
    run_lottery()
    logger.info("Lottery script completed.")
