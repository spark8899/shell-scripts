import requests
from cachetools import TTLCache
from logging_config import get_logger

# CoinGecko API URL
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"

# Set up logging
logger = get_logger(__name__)

# init cache: currency list (TTL is 1 hour), price data (TTL is 5 minutes)
coins_cache = TTLCache(maxsize=1, ttl=3600)  # Update the currency list once an hour
price_cache = TTLCache(maxsize=100, ttl=300)  # 5-minute cache price data

def fetch_coins_list():
    response = requests.get(f"{COINGECKO_API_URL}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1")
    data = response.json()
    coins_cache['coins_list'] = {}
    for coin in data:
        if coin['id'] not in ['batcat', 'bifrost-bridged-eth-bifrost', 'bridged-binance-peg-ethereum-opbnb', 'bifrost-bridged-bnb-bifrost', 'bridged-wrapped-ether-starkgate']:
            coins_cache['coins_list'][coin['id']] = coin['symbol']
    logger.info("Fetched and cached coins list")

def format_price(price, digits=5):
    if abs(price) >= 1:
        # 对于绝对值大于等于1的数，显示2位小数
        return f"{price:.2f}"
    else:
        # 对于绝对值小于1的数，保留第一个非零数字后的指定位数
        abs_price = abs(price)
        if abs_price == 0:
            return "0." + "0" * digits

        # 找到第一个非零数字的位置
        first_non_zero = 0
        while abs_price < 0.1:
            abs_price *= 10
            first_non_zero += 1

        # 构建格式字符串，多保留几位以确保精度
        format_string = f"{{:.{first_non_zero + digits + 5}f}}"
        formatted = format_string.format(abs(price))

        # 截取到指定位数
        decimal_part = formatted.split('.')[1]
        formatted = "0." + decimal_part[:first_non_zero + digits]

        # 去掉末尾的零，但保留小数点
        formatted = formatted.rstrip('0')
        if formatted.endswith('.'):
            formatted += '0'

        # 如果原数是负数，添加负号
        return "-" + formatted if price < 0 else formatted

def get_crypto_data(coin_id, symbol: str):
    try:
        if symbol in price_cache:
            logger.info(f"Cache hit for {symbol}")
            return price_cache[symbol]

        # Get price data from CoinGecko API
        response = requests.get(f"{COINGECKO_API_URL}/coins/{coin_id}")
        data = response.json()

        if not data:
            return None

        # logger.info(f"COINGECKO_DATA, price_change_24h: {data['market_data']['price_change_percentage_24h']}, current_price: {data['market_data']['current_price']['usd']}, high_24h: {data['market_data']['high_24h']['usd']}, low_24h: {data['market_data']['low_24h']['usd']}")
        price_change_24h = data['market_data']['price_change_percentage_24h']
        price_change_24h = f"+{price_change_24h:.2f}" if price_change_24h > 0 else f"{price_change_24h:.2f}"
        current_price = data['market_data']['current_price']['usd']
        current_price = current_price if current_price > 1 else format_price(current_price, 5)
        high_24h = data['market_data']['high_24h']['usd']
        high_24h = high_24h if high_24h > 1 else format_price(high_24h, 5)
        low_24h = data['market_data']['low_24h']['usd']
        low_24h = low_24h if low_24h > 1 else format_price(low_24h, 5)
        crypto_data = {
            'id': data['id'],
            'name': data['name'],
            'symbol': data['symbol'].upper(),
            'current_price': current_price,
            'price_change_24h': price_change_24h,
            'high_24h': high_24h,
            'low_24h': low_24h
        }
        price_cache[symbol] = crypto_data
        logger.info(f"Cache set for {symbol}")
        return crypto_data

    except Exception as e:
        logger.error(f"Error fetching cryptocurrency: {e}")
        return None

def query_crypt_price(code):
    # Find cryptocurrency symbols in messages
    coins_list = coins_cache['coins_list']
    coin_id, symbol = None, None
    if code in coins_list:
        coin_id, symbol = code, coins_list[code]
    else:
        for cid, sym in coins_list.items():
            if sym == code:
                coin_id, symbol = cid, sym
                break

    logger.info(f"coin_id: {coin_id}, symbol: {symbol}")
    if coin_id:
        crypto_data = get_crypto_data(coin_id, symbol)
        logger.info(f"crypto_data_format {crypto_data}")
        if crypto_data:
            change_text = "📈" if crypto_data['price_change_24h'][0] == '+'  else "📉"
            message = (
                f"*{crypto_data['symbol']}/USDT Spot Market Data*\n\n"
                f"💰Current Price: {crypto_data['current_price']} USDT\n"
                f"{change_text}24h Change: {crypto_data['price_change_24h']}%\n"
                f"⬆️24h High: {crypto_data['high_24h']} USDT\n"
                f"⬇️24h Low:  {crypto_data['low_24h']} USDT\n\n"
                f"Start trading on [Topp](https://Topp.io)🚀"
            )
            return message
    else:
        return ''
