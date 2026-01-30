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

import copy
import enum
import json
import os
import platform
import re
import threading
import time
from datetime import timedelta
from typing import Callable, List

import filelock
import urllib3

from _core.constants import ConfigConst, FilePermission
from _core.logger import platform_logger
from _core.utils import get_cst_time, get_user_id
from _core.variables import Variables
try:
    from .db import create_db_and_tables, create_event, delete_events, \
        get_events, update_events_as_uploaded, EventData, sqlite_file_name
    _db_dependency_ok = True
except ModuleNotFoundError:
    _db_dependency_ok = False

__all__ = ['TrackEvent', 'Tracker']

LOG = platform_logger('Analysis')

temp_path = Variables.temp_dir
lock_file = os.path.join(temp_path, '.lock_file')
# 屏蔽TLS警告日志
urllib3.disable_warnings()


def is_valid_time_expr(expr: str):
    return re.match(r'(\d+)([dDhHmM])', expr)


def get_analysis_config():
    cfg = Variables.config.analysis
    cleanup = cfg.get(ConfigConst.cleanup)
    if not cleanup or not is_valid_time_expr(cleanup):
        cleanup = '5d'
    upload = cfg.get(ConfigConst.upload) or {}
    upload_enable = str(upload.get(ConfigConst.tag_enable)).lower()
    if upload_enable not in ['false', 'true']:
        upload_enable = 'true'
    upload_before = upload.get(ConfigConst.before)
    if not upload_before or not is_valid_time_expr(upload_before):
        # 2d默认值为24h
        upload_before = '24h'
    collapse = str(cfg.get(ConfigConst.collapse)).lower()
    if collapse not in ['false', 'true']:
        # 2d默认值true（聚合）
        collapse = 'true'
    return {
        ConfigConst.cleanup: cleanup,
        ConfigConst.upload: {
            ConfigConst.tag_enable: upload_enable,
            ConfigConst.before: upload_before,
            ConfigConst.collapse: collapse,
        }
    }


def get_file_lock():
    if filelock.__version__ < '3.13.0':
        return filelock.FileLock(lock_file, timeout=2)
    return filelock.FileLock(lock_file, timeout=2, is_singleton=True)


def get_time_ago(expr: str):
    """获取单位时间前的时间点
    Example:
        get_time_ago('4h')，获取4小时前的时间点
        get_time_ago('4m')，获取4分钟前的时间点
    """
    now = get_cst_time()
    if expr == ConfigConst.now:
        return now
    ret = is_valid_time_expr(expr)
    if not ret:
        return now
    number, unit = int(ret.group(1)), ret.group(2).lower()
    if unit == 'd':
        td = timedelta(days=number)
    elif unit == 'h':
        td = timedelta(hours=number)
    else:
        td = timedelta(minutes=number)
    return now - td


class TrackEvent(enum.Enum):
    TestTask = '907001001'  # 框架启动
    TestCase = '907001002'  # 用例执行
    TestTaskDebug = '907001003'  # 环境池调试
    AppInfo = '907001004'  # 应用信息
    LoopTest = '907001005'  # 切片执行
    TestDriver = '907001006'  # 测试驱动

    harmony_default = '907001001'

    CaseUiAdaptive = '907003001'     # 用例触发UI自适应
    StepUiAdaptive = '907003002'  # 步骤自适应
    PopHandle = '907003003'

    AiAction = '907003005'          # 触发ai_action
    AiActionAdaptive = '907003006'  # 触发ai_action 但走传统逻辑成功
    AiActionAI = '907003007'        # 触发ai_action 且走AI逻辑成功


class Tracker:
    __analysis_url = ''
    __analysis_testing_url = ''
    __analysis_testing_token = ''
    __events = []
    __init_flag = False
    __privacy_enable = True
    config = {}
    user_id = ''
    product_name = 'xDevice'
    product_version = ''
    test_platform = platform.system()

    @classmethod
    def __initialize__(cls):
        if cls.__init_flag:
            return
        LOG.debug('init tracker')
        if _db_dependency_ok:
            if not os.path.exists(sqlite_file_name):
                try:
                    with get_file_lock():
                        create_db_and_tables()
                except filelock.Timeout:
                    LOG.debug('Get filelock timeout, create db failed')
                except Exception as e:
                    LOG.warning(e)
        else:
            LOG.warning('tracker dependency is not ok')
        from xdevice import VERSION
        cls.product_version = VERSION
        cls.user_id = get_user_id(pass_through=Variables.config.pass_through)
        cls.update_analysis_config()
        cls.__init_flag = True
        LOG.debug('init tracker ended')

    @classmethod
    def update_analysis_config(cls):
        """更新打点配置参数"""
        cls.config = get_analysis_config()

    @classmethod
    def set_analysis_url(cls, url: str):
        if isinstance(url, str) and url:
            cls.__analysis_url = url

    @classmethod
    def set_testing_analysis_config(cls, url: str, token: str):
        if isinstance(url, str) and url:
            cls.__analysis_testing_url = url
        if isinstance(token, str) and token:
            cls.__analysis_testing_token = token

    @classmethod
    def set_privacy_enable(cls, enable: bool):
        if isinstance(enable, bool) and enable:
            cls.__privacy_enable = enable

    @classmethod
    def event(cls, event_id: str, event_name: str = '', **kwargs):
        """make track event
        kwargs:
            product_name: product name
            product_version: product version
        Example:
            Tracker.event(event_id)
            Tracker.event(event_id, event_name='event name')
        """
        if not _db_dependency_ok:
            return
        try:
            cls.__initialize__()
            LOG.debug('Tracking event')
            product_name = kwargs.get('product_name', '') or cls.product_name
            product_version = kwargs.get('product_version', '') or cls.product_version
            data = EventData(
                event_id=str(event_id),
                event_name=str(event_name),
                user_id=cls.user_id,
                product_name=product_name,
                product_version=product_version,
            )
            extras = kwargs.get('extraData')
            if extras and isinstance(extras, dict):
                data.extras = extras
            cls.__events.append(data)
            if len(cls.__events) < 10:
                return
            with get_file_lock():
                create_event(cls.__events)
                cls.__events.clear()
        except filelock.Timeout:
            LOG.debug('Get filelock timeout, tracking event failed')
        except Exception as e:
            LOG.warning(e)

    @classmethod
    def upload(cls, before: str = '', handle_func: Callable = None, wait_result: bool = False):
        """upload track datas
        Example:
            Tracker.upload()
            立即上报：
            Tracker.upload(before='now')
            上报5小时前的数据：
            Tracker.upload(before='5h')
            上报5分钟前的数据：
            Tracker.upload(before='5m')
        """
        if not _db_dependency_ok:
            return
        for i in range(3):
            try:
                if cls.__events:
                    with get_file_lock():
                        create_event(cls.__events)
                    break
            except filelock.Timeout:
                if i < 2:
                    LOG.debug('Get filelock timeout, do retry')
                    time.sleep(1)
                else:
                    LOG.debug('Get filelock timeout, tracking event failed')
            except Exception as e:
                LOG.warning(e)
        handlers = []
        handlers.append(cls.__upload_testing)
        if handle_func and callable(handle_func):
            handlers.append(handle_func)
        th = threading.Thread(target=cls.__do_upload, args=(before.strip(), handlers,))
        th.daemon = False
        th.start()
        if wait_result:
            th.join()

    @classmethod
    def __do_upload(cls, before: str, handlers: List[Callable] = None):
        if not before or before != ConfigConst.now and is_valid_time_expr(before):
            before = cls.config.get(ConfigConst.upload).get(ConfigConst.before)
        cleanup_before = cls.config.get(ConfigConst.cleanup)
        enable1 = (Variables.config.uploadtrack.get(ConfigConst.tag_uploadtrack) or 'true').lower() == 'true'
        enable2 = cls.config.get(ConfigConst.upload).get(ConfigConst.tag_enable).lower() == 'true'
        upload_enable = enable1 and enable2 and cls.__privacy_enable
        try:
            with get_file_lock():
                events = get_events(get_time_ago(before))
                if events and upload_enable:
                    LOG.debug('Upload analysis data')
                    results = []
                    for hdl in handlers:
                        results.append(hdl(events))
                    if True in results:
                        update_events_as_uploaded(events)
                else:
                    LOG.debug('No need to upload analysis data')
            # 删除x天前的记录
                delete_events(get_time_ago(cleanup_before))
        except filelock.Timeout:
            LOG.debug('Get filelock timeout, upload analysis data on next task')
        except Exception as e:
            LOG.warning(e)

    @classmethod
    def __handle_events(cls, events):
        collapse = cls.config.get(ConfigConst.upload).get(ConfigConst.collapse).lower() == 'true'
        datas = []
        for e in events:
            event_id = e.event_id
            event_name = e.event_name
            timestamp = e.created_at.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            user_id = e.user_id
            extras = e.extras
            # 不合并记录
            if not collapse:
                datas.append({
                    'eventId': event_id,
                    'eventName': event_name,
                    'userId': user_id,
                    'happenTime': timestamp,
                    'platform': cls.test_platform,
                    'productName': cls.product_name,
                    'productVersion': cls.product_version,
                    'serviceName': cls.product_name,
                    'serviceVersion': cls.product_version,
                    'extraData': extras,
                })
                continue
            # 合并记录
            matched = None
            for d in datas:
                if d.get('eventId') != event_id or d.get('userId') != user_id:
                    continue
                # 若是AppInfo的记录，还需匹配应用包名
                if event_id != TrackEvent.AppInfo.value \
                        or d.get('extraData').get('bundle_name', '') == extras.get('bundle_name', ''):
                    matched = d
                    break
            if matched:
                extra_data = matched.get('extraData')
                extra_data.update({'count': extra_data.get('count') + 1})
            else:
                extra_data = {
                    'count': 1,
                }
                if event_id == TrackEvent.AppInfo.value:
                    extra_data.update({'bundle_name': extras.get('bundle_name') or ''})
                data = {
                    'eventId': event_id,
                    'eventName': event_name,
                    'userId': user_id,
                    'happenTime': timestamp,
                    'platform': cls.test_platform,
                    'productName': cls.product_name,
                    'productVersion': cls.product_version,
                    'serviceName': cls.product_name,
                    'serviceVersion': cls.product_version,
                    'extraData': extra_data
                }
                datas.append(data)
        return datas


    @classmethod
    def __upload_testing(cls, events):
        datas = cls.__handle_events(events)
        track_data_name = 'tracker_data_' + get_cst_time().strftime('%Y%m%d%H%M%S')
        track_data_file = os.path.join(temp_path, track_data_name)
        data_fd = os.open(track_data_file, os.O_WRONLY | os.O_CREAT, FilePermission.mode_644)
        with os.fdopen(data_fd, mode='w', encoding='utf-8') as f:
            for d in datas:
                f.write(json.dumps(d, ensure_ascii=False) + '\n')
        from .testing import TestingUploader
        ret = TestingUploader(url=cls.__analysis_testing_url, auth=cls.__analysis_testing_token).upload(track_data_file)
        if os.path.exists(track_data_file):
            os.remove(track_data_file)
        # 清理残留的打点数据文件
        for filename in os.listdir(temp_path):
            filepath = os.path.join(temp_path, filename)
            if os.path.isfile(filepath) and filename.startswith('tracker_data_') \
                    and int((time.time() - os.stat(filepath).st_mtime) / 86400) > 1:
                os.remove(filepath)
        return ret

    @classmethod
    def __upload_wisecloud(cls, events):
        from .wisecloud import WiseCloudUploader, generate_random_string
        header = {
            'appid': 'com.hmos.hypium',
            'chifer': '',
            'compress_mode': '1',
            'eventType': '0',
            'hmac': '',
            'packageName': 'hypium',
            'protocol_version': '1',
            'requestid': generate_random_string(),
            'serviceid': 'com.hmos.hypium',
            'servicetag': 'hypium',
        }
        datas = []
        for data in cls.__handle_events(events):
            datas.append({
                'header': header,
                'event': json.dumps(data),
            })
        return WiseCloudUploader(cls.__analysis_url).upload(datas)
