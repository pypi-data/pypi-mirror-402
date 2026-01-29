# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import sys

from typing import List

from alibabacloud_dysmsapi20170525.client import Client as DysmsapiClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_models
from alibabacloud_tea_util.client import Client as UtilClient
import json
from ks_utility import datetimes
from ks_utility.constants import RET_OK, RET_ERROR
from ks_utility.object import BaseException

from enum import Enum

class SmsStatus(Enum):
    SENDING = '发送中'
    OK = '发送成功'
    ERROR = '发送失败'


class SmsClient():
    def __init__(self, access_key_id: str, access_key_secret: str):
        self.client = self.create_client(access_key_id, access_key_secret)

    def create_client(
        self,
        access_key_id: str,
        access_key_secret: str,
    ) -> DysmsapiClient:
        """
        使用AK&SK初始化账号Client
        """
        config = open_api_models.Config()
        config.access_key_id = access_key_id
        config.access_key_secret = access_key_secret
        return DysmsapiClient(config)

    # 20240830开始停止维护
    def send_sms(
        self,
        phone_numbers: str,
        sign_name: str,
        template_code: str,
        template_param: str
    ) -> None:
        client = self.client
        # 1.发送短信
        send_req = dysmsapi_models.SendSmsRequest(
            phone_numbers=phone_numbers,
            sign_name=sign_name,
            template_code=template_code,
            template_param=template_param
        )
        send_resp = client.send_sms(send_req)
        code = send_resp.body.code
        if not UtilClient.equal_string(code, 'OK'):
            return RET_ERROR, f'msg:{send_resp.body.message};request_id:{send_resp.body.request_id}'

        biz_id = send_resp.body.biz_id
        return RET_OK, biz_id
    
    def send(
        self,
        phone_numbers: str,
        sign_name: str,
        template_code: str,
        template_params: dict
    ) -> None:
        client = self.client
        # 1.发送短信
        send_req = dysmsapi_models.SendSmsRequest(
            phone_numbers=phone_numbers,
            sign_name=sign_name,
            template_code=template_code,
            template_param=json.dumps(template_params)
        )
        send_resp = client.send_sms(send_req)
        code = send_resp.body.code
        biz_id = send_resp.body.biz_id
        if not UtilClient.equal_string(code, 'OK'):
            raise BaseException(
                message=send_resp.body.message,
                data={
                    'request_id': send_resp.body.request_id,
                    'biz_id': biz_id,
                    'phone_numbers': phone_numbers,
                    'sign_name': sign_name,
                    'template_code': template_code,
                    'template_params': template_params,     
                }) 
        return biz_id
        

    def query_sms(self, biz_id: str, phone_numbers: str):
        if not biz_id:
            return
        
        client = self.client
        statuses: list[dict] = []

        # 3.查询结果
        phone_nums = phone_numbers.split(',')
        for phone_num in phone_nums:
            query_req = dysmsapi_models.QuerySendDetailsRequest(
                phone_number=UtilClient.assert_as_string(phone_num),
                biz_id=biz_id,
                send_date=datetimes.now().strftime('%Y%m%d'),
                page_size=10,
                current_page=1   
            )
            query_resp = client.query_send_details(query_req)
            dtos = query_resp.body.sms_send_detail_dtos.sms_send_detail_dto
            # 打印结果
            for dto in dtos:
                if UtilClient.equal_string(f'{dto.send_status}', '3'):
                    status = SmsStatus.OK
                elif UtilClient.equal_string(f'{dto.send_status}', '2'):
                    status = SmsStatus.ERROR
                else:
                    status = SmsStatus.SENDING
        
            statuses.append({
                'phone_number': dto.phone_num,
                'status': status,
                'datetime': dto.receive_date
            })

        return statuses
    
    def query(self, biz_id: str, phone_numbers: str):
        return self.query_sms(biz_id=biz_id, phone_numbers=phone_numbers)
    
from typing import  Tuple
from alibabacloud_cams20200606.client import Client as cams20200606Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_cams20200606 import models as cams_20200606_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

class WhatsAppClient:
    def __init__(self, access_key_id: str, access_key_secret: str):
        self.client = WhatsAppClient.create_client(access_key_id, access_key_secret)

    @staticmethod
    def create_client(
        access_key_id: str,
        access_key_secret: str
    ) -> cams20200606Client:
        """
        使用AK&SK初始化账号Client
        @return: Client
        @throws Exception
        """
        # 工程代码泄露可能会导致 AccessKey 泄露，并威胁账号下所有资源的安全性。以下代码示例仅供参考。
        # 建议使用更安全的 STS 方式，更多鉴权访问方式请参见：https://help.aliyun.com/document_detail/378659.html。
        config = open_api_models.Config(
            # 必填，请确保代码运行环境设置了环境变量 ALIBABA_CLOUD_ACCESS_KEY_ID。,
            access_key_id=access_key_id,
            # 必填，请确保代码运行环境设置了环境变量 ALIBABA_CLOUD_ACCESS_KEY_SECRET。,
            access_key_secret=access_key_secret
        )
        # Endpoint 请参考 https://api.aliyun.com/product/cams
        config.endpoint = f'cams.ap-southeast-1.aliyuncs.com'
        return cams20200606Client(config)

    def send(
        self,
        phone_numbers: str,
        template_code: str,
        template_params: Tuple[dict, list[dict]], # 传入dict则所有参数一样，传入list，则是每个号码个性化
        from_: str,
        language: str = 'zh_CN'
    ) -> None:
        client = self.client

        senders: list[cams_20200606_models.SendChatappMassMessageRequestSenderList] = []
        numbers: list = phone_numbers.split(',')
        for i, number in enumerate(numbers):
            params: dict = template_params if isinstance(template_params, dict) else template_params[i]
            sender = cams_20200606_models.SendChatappMassMessageRequestSenderList(
                template_params=params,
                to=number
            )
            senders.append(sender)
        send_chatapp_mass_message_request = cams_20200606_models.SendChatappMassMessageRequest(
            sender_list=senders,
            channel_type='whatsapp',
            template_code=template_code,
            language=language,
            from_=from_
        )
        runtime = util_models.RuntimeOptions()
        return client.send_chatapp_mass_message_with_options(send_chatapp_mass_message_request, runtime)

