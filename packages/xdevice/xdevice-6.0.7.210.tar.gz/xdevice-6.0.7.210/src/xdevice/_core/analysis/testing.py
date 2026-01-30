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

import hashlib
import json
import os
import zipfile
from typing import Tuple

import requests
from requests.adapters import HTTPAdapter

from _core.logger import platform_logger

LOG = platform_logger('Analysis')
adapter = HTTPAdapter(max_retries=0)


def xor_encrypt_decrypt(data: bytes):
    key = b'mysecretkey'
    data_len = len(data)
    while len(key) < data_len:
        key = key * 2
    key = key[0: data_len]
    return bytes([x ^ y for x, y in zip(data, key)])


def read_url_auth(filename) -> Tuple[str, str]:
    if not os.path.exists(filename):
        return '', ''
    with open(filename, 'rb') as rfile:
        rfile.seek(10)
        json_bytes = rfile.read()
        json_bytes = xor_encrypt_decrypt(json_bytes)
        json_str = json_bytes.decode('utf-8')
        json_obj = json.loads(json_str)
        return json_obj.get('upload_info_url', ''), json_obj.get('authorization', '')


def md5_sha256_file(file_path):
    if not os.path.exists(file_path):
        return '', ''
    with open(file_path, 'rb') as f:
        read_data = f.read()
        md5_obj = hashlib.md5()
        md5_obj.update(read_data)
        sha256_obj = hashlib.sha256()
        sha256_obj.update(read_data)
    md5_code = md5_obj.hexdigest()
    sha256_code = sha256_obj.hexdigest()
    return md5_code, sha256_code


class TestingUploader:

    def __init__(self, url: str = '', auth: str = ''):
        ulse_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'resource', 'upsec', 'ulse'
        )
        if url and auth:
            self.upload_url, self.auth = url, auth
        else:
            self.upload_url, self.auth = read_url_auth(ulse_file)

    @staticmethod
    def __get_session():
        session = requests.Session()
        session.mount("https://", adapter)
        return session

    def __get_upload_link(self):
        if not self.upload_url or not self.auth:
            LOG.warning('Decryption failed! Cancel upload analysis data')
            return ''
        headers = {
            'Authorization': self.auth,
            'Content-Type': 'application/json;charset=UTF-8'
        }
        rsp = None
        session = None
        upload_link = ''
        try:
            session = self.__get_session()
            verify = True
            rsp = session.get(self.upload_url, headers=headers, verify=verify, timeout=(1, 5))
            upload_link = rsp.json().get('upload_link', '')
        except Exception as e:
            LOG.warning(f'Get analysis data reporting url for Testing failed. {e}')
        finally:
            if rsp:
                rsp.close()
            if session:
                session.close()
        return upload_link

    @staticmethod
    def __gen_zip(record_file, to_path):
        file_name = os.path.basename(record_file)
        with zipfile.ZipFile(to_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(record_file, f'trackerLogs/{file_name}')

    def upload(self, record_file):
        upload_link = self.__get_upload_link()
        if not upload_link:
            return False
        zip_file = record_file + '.zip'
        self.__gen_zip(record_file, zip_file)
        if not os.path.exists(zip_file):
            LOG.warning(f'The zip file {zip_file} does not exist! Will not upload!')
            return False
        md5, sha256 = md5_sha256_file(zip_file)
        url = upload_link + md5

        rsp = None
        ret = False
        headers = {'sha256': sha256, 'Authorization': self.auth}
        with open(zip_file, 'rb') as zipf:
            files = {'file': zipf}
            session = None
            try:
                session = self.__get_session()
                verify = True
                rsp = session.post(url, files=files, headers=headers, timeout=(1, 5), verify=verify)
                code, rsp_msg = rsp.status_code, rsp.content.decode()
                if 'md5' in rsp_msg and 'sha256' in rsp_msg:
                    LOG.debug('Upload analysis data to Testing successful')
                    ret = True
                else:
                    LOG.debug(f'Upload analysis data to Testing failed. {rsp_msg}')
            except Exception as e:
                LOG.warning(f'Upload analysis data to Testing failed. {e}')
            finally:
                if rsp:
                    rsp.close()
                if session:
                    session.close()
        os.remove(zip_file)
        return ret
