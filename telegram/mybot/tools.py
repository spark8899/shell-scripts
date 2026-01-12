import time

from collections import defaultdict, OrderedDict
from config import ALLOWED_GROUP_IDS
from logging_config import get_logger

# Set up logging
logger = get_logger(__name__)

# User request rate limit
USER_RATE_LIMIT = 5  # Maximum number of requests per user per minute
user_request_times = defaultdict(list)

# Simple cache implementation
CACHE_SIZE = 100
cache = OrderedDict()

def is_allowed_chat(chat_id):
    return chat_id in ALLOWED_GROUP_IDS

def rate_limit(user_id):
    current_time = time.time()
    user_request_times[user_id] = [t for t in user_request_times[user_id] if current_time - t < 60]
    user_request_times[user_id].append(current_time)
    return len(user_request_times[user_id]) <= USER_RATE_LIMIT

def get_cached_response(message):
    return cache.get(message)

def cache_response(message, response):
    cache[message] = response
    if len(cache) > CACHE_SIZE:
        cache.popitem(last=False)
