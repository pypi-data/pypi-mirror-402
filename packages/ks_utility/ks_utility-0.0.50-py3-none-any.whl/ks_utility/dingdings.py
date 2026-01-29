import time
import hmac
import hashlib
import base64
import urllib.parse
import urllib.request
from datetime import datetime
import json
import multitasking
from time import sleep

class DingDing():
    def __init__(self, secret, token):
        self.secret = secret
        self.token = token
        self.url = f'https://oapi.dingtalk.com/robot/send?access_token={token}'

        # 每分钟最多20条消息，否则会被限流10分钟
        #https://open.dingtalk.com/document/robots/custom-robot-access
        self.max_num = 20
        self.cur_nums = {}

    def send_request(self, url, datas):
        header = {
            "Content-Type": "application/json",
            "Charset": "UTF-8"
        }
        sendData = json.dumps(datas)
        sendDatas = sendData.encode("utf-8")
        request = urllib.request.Request(url=url, data=sendDatas, headers=header)
        opener = urllib.request.urlopen(request)
        # # 输出响应结果
        # print(opener.read())

    @multitasking.task
    def send(self, text='Hello DD', title='', at_all=False):
        if not self.secret:
            return
        
        # 超过流量限制则过60s再继续推送
        num = self.cur_num()
        if num > self.max_num:
            sleep(60)

        if not title:
            title = text

        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, self.secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        url = self.url + f'&sign={sign}&timestamp={timestamp}'
        # isAtAll：是否@所有人，建议非必要别选，不然测试的时候很尴尬
        dict = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": text
            },
            "at": {
                "isAtAll": False
            }
        }
        self.send_request(url, dict)

    def cur_num(self):
        ts = datetime.now().strftime('%Y-%m-%d %H:%M')
        if not self.cur_nums.get(ts):
            self.cur_nums[ts] = 0

        self.cur_nums[ts] += 1

        return self.cur_nums[ts]


