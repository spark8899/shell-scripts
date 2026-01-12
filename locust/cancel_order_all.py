#!./venv/bin/python3
from functools import partial
from multiprocessing import Pool
import hashlib, requests, time, json

base_url = 'http://gwc.goknn.mm'

def get_sign(str, private_key):
    str_key = "%s&%s" % (str, private_key)
    md5_obj = hashlib.md5()
    str_key_bytes = str_key.encode(encoding='utf-8')
    md5_obj.update(str_key_bytes)
    return md5_obj.hexdigest()

def cancel_order(symbol, tag, api_key, private_key): # symbol first
    params = {
        'api_key': api_key,
        'symbol': symbol,
    }
    timestamp = int(time.time())
    params['time'] = timestamp
    sorted_params = dict(sorted(params.items()))
    payload = '&'.join([f'{param}{value}' for param, value in sorted_params.items()])
    params['sign'] = get_sign(payload, private_key)

    payload_str = '&'.join([f'{param}={value}' for param, value in params.items()])
    headers = {
        'Accept': 'application/json;charset=utf-8'
    }
    response = requests.post(
        "%s/%s?%s" % (base_url, 'api/cancelOrder', payload_str),
        headers=headers,
    )
    print("%s cancle %s, %s" % (tag, symbol, response.json()))



def main():
    with open("acc.json", 'r') as f:
        acc = json.load(f)

    for tag, v in acc.items():
        pool = Pool(5)
        symbol_list = ["DOGEUSDT", "BTCUSDT", "ETHUSDT", "BCHUSDT", "LTCUSDT"]
        par = partial(cancel_order, tag=tag, api_key=v['api_key'], private_key=v['private_key'])
        pool.map(par, symbol_list)

    #for symbol in ["DOGEUSDT", "BTCUSDT", "ETHUSDT", "BCHUSDT", "LTCUSDT"]:
    #    for i, j in acc.items():
    #        print("%s cancel %s order" % (i, symbol))
    #        cancel_order(symbol, j['api_key'], j['private_key'])
    #        print()

if __name__ == '__main__':
    #print("start...")
    main()
    #print("end.....")
