#!/usr/bin/env python3
# coding=utf-8
#
# Copyright (c) Huawei Device Co., Ltd. 2025. All right reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import json
import secrets
import string
import zlib

import requests
from requests.adapters import HTTPAdapter

from _core.logger import platform_logger

LOG = platform_logger('Analysis')

adapter = HTTPAdapter(max_retries=0)


def generate_random_string(length=32):
    """生成指定长度的随机字符串，仅包含大小写字母"""
    alphabet = string.ascii_letters
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class WiseCloudUploader:

    def __init__(self, url: str):
        self.url = url

    def upload(self, data):
        ret = False
        rsp = None
        session = None
        headers = {
            "Content-Type": "application/octet-stream",
            "App-Id": "com.hmos.hypium",
            "request-id": generate_random_string(),
        }
        try:
            compressed_bytes = zlib.compress(json.dumps(data).encode(encoding='utf-8'))
            session = requests.Session()
            session.mount("https://", adapter)
            verify = True
            rsp = session.post(self.url, data=compressed_bytes, headers=headers, timeout=(1, 5), verify=verify)
            code, rsp_msg = rsp.status_code, rsp.content.decode()
            if code == 200:
                LOG.debug('Upload analysis data successful')
                ret = True
            else:
                LOG.debug('Upload analysis data failed')
                LOG.debug(f'response code: {code}')
                LOG.debug(f'response message: {rsp_msg}')
        except requests.exceptions.ConnectTimeout:
            LOG.warning('Connect to server failed')
        except Exception as e:
            LOG.warning(f'Upload analysis data failed. {e}')
        finally:
            if rsp:
                rsp.close()
            if session:
                session.close()
        return ret
