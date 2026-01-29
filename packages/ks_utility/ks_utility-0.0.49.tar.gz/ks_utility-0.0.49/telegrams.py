# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.

from typing import List
from ks_utility.constants import RET_OK, RET_ERROR
import requests

class TelegramException(Exception):
    def __init__(self, message: str, code: str='') -> None:
        super().__init__(message)
        self.code = code

class TelegramBotClient:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id

    def send(self, text, parse_mode='MarkdownV2'):
        url = f'https://api.telegram.org/bot{self.token}/sendMessage'
        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode
        }

        response = requests.post(url, data=payload)
        if not response.status_code == 200:
            raise TelegramException(message=response.text, code=response.status_code)
        return response


