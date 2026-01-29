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
#   File Name : jsonparse.py
#   Repo: https://github.com/LuomingXu/selfusepy

"""
Json to Object的工具库
"""
from dataclasses import fields
from typing import MutableMapping, Any, Type, get_type_hints, get_origin, get_args

class_dict = {}
__classname__: str = '__classname__'


class BaseJsonObject(object):
    """
    用于在用户自定义Json的转化目标类的基类
    以是否为此基类的子类来判断这个类是否需要转化
    """
    pass


class ClassField(object):

    def __init__(self, varname: str = None, ignore: bool = False, func = None):
        self.varname: str = varname  # object's var's name
        self.ignore: bool = ignore  # do not convert this field
        self.handle_func = func  # handle function for this variable


def DeserializeConfig(_map: MutableMapping[str, ClassField]):
    """
    :param _map: key->json key, value->annotation
    :return:
    """

    def func(clazz):
        def get_annotation(self, k: str = None) -> ClassField | MutableMapping[str, ClassField]:
            return _map.get(k) if k else _map

        clazz.get_annotation = get_annotation
        return clazz

    return func


"""
Archive
```python
def JSONField(key_variable: dict):
  def func(cls):
    @override_str
    class NoUseClass(BaseJsonObject):
      def __init__(self, *args, **kwargs):
        self = cls(*args, **kwargs)

      @classmethod
      def json_key_2_variable_name(cls, k: str):
        return key_variable.get(k)

    return NoUseClass

  return func
```
"""


def _deserialize_object(d: dict) -> object | dict:
    """
    用于json.loads()函数中的object_hook参数
    :param d: json转化过程中的字典
    :return: object
    """
    cls_name = d.pop(__classname__, None)
    cls = class_dict.get(cls_name)
    field_names = [item.name for item in fields(cls)]
    if cls:
        obj = cls.__new__(cls)  # Make instance without calling __init__
        flag = hasattr(obj, 'get_annotation')
        for key, value in d.items():
            if flag:  # 判断是否有ClassField注解
                res: ClassField = obj.get_annotation(key)
                if res:  # 判断这个key是否配置了注解
                    if res.ignore:
                        continue
                    if res.varname:
                        key = res.varname
                    if res.handle_func:
                        value = res.handle_func(value)
            if not any(key == item for item in field_names):
                continue
            setattr(obj, key, value)
        return obj
    else:
        return d


def _add_classname(d: dict, t: Type) -> dict:
    """
    给json字符串添加一个"__classname__"的key来作为转化的标志
    :param d: json的字典
    :param classname: 转化的目标类
    :return: 修改完后的json dict
    """
    if get_origin(t) is list:
        t = get_args(t)[0]
    type_hints = get_type_hints(t)
    d[__classname__] = t.__name__

    for k, v in d.items():
        if isinstance(v, dict):
            _add_classname(v, type_hints.get(k))
        elif isinstance(v, list):
            for item in v:
                # 如果这个list是基本类型(int, str...)之类则不需要添加classname
                if any(isinstance(item, tp) for tp in (int, str, bool, float, complex)):
                    break
                _add_classname(item, type_hints.get(k))

    return d


def _add_classname_list(l: list, classname: Type) -> list:
    for d in l:
        _add_classname(d, classname)
    return l


def _safe_issubclass(tp: Any, cls: Type):
    """
    安全判断 tp 是否是 cls 的子类。
    防止出现判断{_GenericAlias}typing.List[str]报错

    参数：
        tp: 待判断对象，可能是 class，也可能是 typing 泛型等任意类型
        cls: 目标类

    返回：
        bool: 如果 tp 是 cls 的子类返回 True，否则返回 False。
              如果 tp 不是 class 类型，返回 False，不会抛异常。
    """
    try:
        return issubclass(tp, cls)
    except TypeError:
        return False


def _generate_class_dict(obj: BaseJsonObject):
    """
    构造需要转化的目标类的所包含的所有类
    将key: 类名, value: class存入class_dict中
    :param obj: 目标类
    """
    cls = type(obj)
    class_dict[cls.__name__] = cls
    type_hints = get_type_hints(cls)
    for k, cls in type_hints.items():
        if _safe_issubclass(cls, BaseJsonObject):
            _generate_class_dict(cls())
        elif get_origin(cls) is list:
            cls = get_args(cls)[0]
            if _safe_issubclass(cls, BaseJsonObject):
                _generate_class_dict(cls())
