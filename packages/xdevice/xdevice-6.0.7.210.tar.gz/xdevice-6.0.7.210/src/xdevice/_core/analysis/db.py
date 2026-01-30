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

import os
from datetime import datetime
from typing import Any, Dict, List, Union

from sqlmodel import create_engine, select, Field, JSON, Session, SQLModel

from _core.utils import get_uid
from _core.variables import Variables

temp_path = Variables.temp_dir
sqlite_file_name = os.path.join(temp_path, f'events_{get_uid()}.db')
sqlite_url = f'sqlite:///{sqlite_file_name}'


class EventData(SQLModel, table=True):
    id: Union[int, None] = Field(default=None, primary_key=True, description='记录ID')
    event_id: str = Field(index=True, description='事件ID')
    event_name: str = Field(default='', description='事件名称')
    user_id: str = Field(index=True, description='用户ID')
    product_name: str = Field(default='xDevice', description='产品名称')
    product_version: str = Field(description='产品版本')
    uploaded: int = Field(default=0, description='上报标记')
    extras: Dict[str, Any] = Field(default={}, sa_type=JSON, description='扩展信息')
    created_at: datetime = Field(default_factory=datetime.now, description='创建时间')
    updated_at: datetime = Field(default_factory=datetime.now, description='更新时间',
                                 sa_column_kwargs={"onupdate": datetime.now})


engine = create_engine(
    sqlite_url,
    connect_args={'check_same_thread': False}
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def create_event(data: Union[EventData, List[EventData]]):
    with Session(engine) as session:
        if isinstance(data, list):
            session.add_all(data)
        else:
            session.add(data)
        session.commit()


def delete_events(dt: datetime):
    statement = select(EventData).where(EventData.created_at <= dt)
    with Session(engine) as session:
        results = session.exec(statement).all()
        if not results:
            return
        for r in results:
            session.delete(r)
            session.commit()


def get_events(dt: datetime) -> List[EventData]:
    statement = select(EventData) \
        .where(EventData.created_at <= dt) \
        .where(EventData.uploaded == 0)
    with Session(engine) as session:
        return session.exec(statement).all()


def update_events_as_uploaded(datas: List[EventData]):
    if not datas:
        return
    with Session(engine) as session:
        for d in datas:
            d.uploaded = 1
            session.add(d)
            session.commit()
