#    Copyright 2018-2020 LuomingXu
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#   Author : Luoming Xu
#   File Name : __init__.py
#   Repo: https://github.com/LuomingXu/selfusepy

import json
from datetime import datetime, timezone, timedelta
from typing import TypeVar, List

from .jsonparse import BaseJsonObject, ClassField, DeserializeConfig
from .log import Logger
from .utils import eprint, override_str, ShowProcess, lookahead

__all__ = ["BaseJsonObject", "ClassField", "DeserializeConfig", "Logger", "eprint", "override_str", "ShowProcess",
           "lookahead"]

__version__ = '0.4.0'

T = TypeVar('T')


def fromtimestamp(timestamp: float, offset: int) -> datetime:
    return datetime.fromtimestamp(timestamp, timezone(timedelta(hours=offset)))


def now(offset: int):
    return datetime.now(timezone(timedelta(hours=offset)))


def parse_json(j: str | bytes | bytearray, obj: T) -> T:
    """
    Json to Python Object
    >>>import selfusepy
    >>>obj: T = selfusepy.parse_json(jsonStr, Obj())
    :param j: json format obj
    :param obj: Py Object
    :return: obj
    """

    jsonparse._generate_class_dict(obj)
    json_dict: dict = json.loads(j)
    j_modified: str = json.dumps(jsonparse._add_classname(json_dict, type(obj)))
    res = json.loads(j_modified, object_hook=jsonparse._deserialize_object)

    jsonparse.class_dict.clear()
    return res


def parse_json_array(j: str, obj: T) -> List[T]:
    """
    Json array to List
    """
    jsonparse._generate_class_dict(obj)
    json_list: list = json.loads(j)
    j_modified: str = json.dumps(jsonparse._add_classname_list(json_list, type(obj)))
    res = json.loads(j_modified, object_hook=jsonparse._deserialize_object)

    jsonparse.class_dict.clear()
    return res
