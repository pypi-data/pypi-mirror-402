#!/usr/bin/env python3
# coding=utf-8

#
# Copyright (c) 2020-2022 Huawei Device Co., Ltd.
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
import os
import stat

from setuptools import setup

INSTALL_REQUIRES = [
    "filelock",
    "paramiko",
    "pyserial",
    "requests",
    "sqlmodel;platform_system!='HarmonyOS'",
    # urllib3的2.1以上版本，匹配python3.8，而当前工具支持的最低python版本是3.7，故约束此依赖
    "urllib3<2.1;python_version<'3.8'"
]


def get_info(file_path):
    ver = "0.0.0"
    try:
        ver_file_open = os.open(file_path,
                                os.O_RDWR, stat.S_IWUSR | stat.S_IRUSR)
        with os.fdopen(ver_file_open, "r", encoding="utf-8") as file_desc:
            lines = file_desc.readlines()
            for line in lines:
                if line.strip().startswith("VERSION"):
                    ver = line.split("=")[1].strip()
                    ver = ver.replace("'", "").replace('"', "")
    except Exception as e:
        ver = "0.0.0"
    return ver


version = get_info("src/xdevice/__init__.py")
setup(
    name='xdevice',
    description='xdevice test framework',
    url='',
    version=version,
    package_dir={'': 'src'},
    packages=[
        'xdevice',
        'xdevice._core',
        'xdevice._core.command',
        'xdevice._core.config',
        'xdevice._core.driver',
        'xdevice._core.environment',
        'xdevice._core.executor',
        'xdevice._core.report',
        'xdevice._core.testkit',
        'xdevice._core.context',
        'xdevice._core.cluster',
        'xdevice._core.cluster.controller',
        'xdevice._core.cluster.worker',
        'xdevice._core.analysis',
    ],
    package_data={
        'xdevice._core': [
            'resource/*.txt',
            'resource/config/*.xml',
            'resource/template/*',
            'resource/template/static/*',
            'resource/template/static/components/*',
            'resource/template/static/css/*',
            'resource/tools/*',
        ]
    },
    entry_points={
        'console_scripts': [
            'xdevice=xdevice.__main__:main_process',
            'xdevice_report=xdevice._core.report.__main__:main_report'
        ]
    },
    zip_safe=False,
    install_requires=INSTALL_REQUIRES,
    extras_require={
        "full": [
            "cryptography",
            "psutil",
            "fastapi;python_version>='3.10'",
            "python-multipart;python_version>='3.10'",
            "uvicorn;python_version>='3.10'"
        ]
    },
)
