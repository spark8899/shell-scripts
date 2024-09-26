from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error, pooling
from cachetools import TTLCache
from logging_config import get_logger
from config import DBCONFIG

# Set up logging
logger = get_logger(__name__)

# init cache: config list (TTL is 1 hour)
config_cache = TTLCache(maxsize=1, ttl=3600)  # Update the config list once an hour

# Create a connection pool
connection_pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **DBCONFIG)

# Function to get guessing configuration from the database or cache
def get_guessing_config():
    # Check if the cached config is still valid
    if 'config' in config_cache :
        return config_cache['config']
    else:
        # If cache is invalid, fetch config from database
        connection = connection_pool.get_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT config_name, config_value FROM my_config")
            config_data = cursor.fetchall()
            cursor.close()
            connection.close()

        config_dict = {name: value for name, value in config_data}
        config_cache['config'] = config_dict
        return config_cache['config']

# Check if the current time is within the guessing period
def is_within_guessing_period():
    config = get_guessing_config()
    start_time = datetime.fromisoformat(config['guess_start_time'])
    end_time = datetime.fromisoformat(config['guess_end_time'])
    current_time = datetime.now()
    return start_time <= current_time <= end_time

def post_guess(user_id, user_name, guess_content):
    # Check if the current time is within the guessing period
    if not is_within_guessing_period():
        return "You can only submit guesses during the time period."

    config = get_guessing_config()

    # Check if the user has already made a guess in the current week
    connection = connection_pool.get_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM my_guesses WHERE user_id = %s AND guess_tag = %s AND guess_time BETWEEN %s AND %s",
            (user_id, config['guess_tag'], config['guess_start_time'], config['guess_end_time'])
        )
        count = cursor.fetchone()[0]
        cursor.close()
        connection.close()

        if count > 0:
            return "You're in, follow pined for other events!"

    # Save guess to database
    connection = connection_pool.get_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO my_guesses (user_id, user_name, guess_content, guess_tag, guess_time) VALUES (%s, %s, %s, %s, %s)",
            (user_id, user_name, guess_content, config['guess_tag'], datetime.now())
        )
        connection.commit()
        cursor.close()
        connection.close()

    # return success.
    logger.info(f"`{user_name}`(`user_id`) comit guess: `{guess_content}`")
    return "You have submitted, thank you for participating"
