import hashlib, time, random, string
from locust.contrib.fasthttp import FastHttpUser
from locust import HttpUser, TaskSet, task
import queue

def get_sign(str, private_key):
    str_key = "%s&%s" % (str, private_key)
    md5_obj = hashlib.md5()
    str_key_bytes = str_key.encode(encoding='utf-8')
    md5_obj.update(str_key_bytes)
    return md5_obj.hexdigest()

def get_payload_str(symbol, volume, side, type, api_key, private_key, price):
    capital_pword = ''.join(random.sample(string.ascii_letters + string.digits, 8))
    params = {
        'symbol': symbol,
        'volume': volume,
        'side': side,
        'type': type,
        'api_key': api_key,
        'capital_pword': capital_pword,
        'fee_is_user_exchange_coin': '1',
        'source': 'API',
    }
    if price != '':
        params['price'] = price
    timestamp = int(time.time())
    params['time'] = timestamp
    sorted_params = dict(sorted(params.items()))
    payload = '&'.join([f'{param}{value}' for param, value in sorted_params.items()])
    params['sign'] = get_sign(payload, private_key)

    payload_str = '&'.join([f'{param}={value}' for param, value in params.items()])
    return payload_str

class OrderTest(TaskSet):
    def on_start(self):
        try:
            data = self.user.queueData.get()
        except queue.Empty:
            print("no data exit")
            exit(0)
        self.user_id, self.vle, self.api_key, self.private_key = data['user_id'], data['vle'], data['api_key'], data['private_key']
        self.order_total, self.order_success = 0, 0
        self.start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print("%s start..." % self.user_id)

    def on_stop(self):
        print("%s stop, start_time: %s, stop_time: %s, total: %d, success: %d" % (self.user_id, self.start_time, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                                                                  self.order_total, self.order_success))

    @task()
    def test_createOrder(self):
        # market order
        volume = "5" # "%s%s" % ('200.', ''.join(random.sample(string.digits, 4)))
        symbol, volume, side, type, price = 'DOGEUSDT', volume, 'BUY', '2', ''

        # limit order
        #volume = "5" # "%s%s" % (self.vle, ''.join(random.sample(string.digits, 4)))
        #symbol, volume, side, type, price = 'DOGEUSDT', volume, 'BUY', '1', '0.05'

        payload_str = get_payload_str(symbol, volume, side, type, self.api_key, self.private_key, price)
        with self.client.post("/%s?%s" % ('api/createOrder', payload_str), catch_response=True) as resp:
            self.order_total = self.order_total + 1
            if resp.status_code == 200 and resp.json()['code'] == '0':
                res = resp.json()
                self.order_id, self.order_success = res['data']['order_id'], self.order_success + 1
                #print("%s Create order successfully, time: %s, volume: %s, order_id: %s" % (self.user_id, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), volume, self.order_id))
                resp.success()
            else:
                print("%s Failed create order, error code: %s" %(self.user_id, resp.json()['code']))
                resp.failure("%s Failed create order, code: %s" %(self.user_id, resp.json()['code']))

class Tt(FastHttpUser):
    tasks = [OrderTest]
    host = 'http://127.0.0.1:8090'
    min_wait = 1000
    max_wait = 5000
    queueData = queue.Queue()
    tt01 = {'user_id': 't01', 'api_key': 'aaaaaaabbbbbbb', 'private_key': 'cccccccccddddddd'}
    tt02 = {'user_id': 't02', 'api_key': 'aaaaaaabbbbbbb', 'private_key': 'cccccccccddddddd'}
    tt03 = {'user_id': 't03', 'api_key': 'aaaaaaabbbbbbb', 'private_key': 'cccccccccddddddd'}
    tt04 = {'user_id': 't04', 'api_key': 'aaaaaaabbbbbbb', 'private_key': 'cccccccccddddddd'}
    tt05 = {'user_id': 't05', 'api_key': 'aaaaaaabbbbbbb', 'private_key': 'cccccccccddddddd'}
    queueData.put_nowait(t01)
    queueData.put_nowait(t02)
    queueData.put_nowait(t03)
    queueData.put_nowait(t04)
    queueData.put_nowait(t05)
