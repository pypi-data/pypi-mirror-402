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
#   File Name : utils.py
#   Repo: https://github.com/LuomingXu/selfusepy

import ctypes
import inspect
import os
import sys
from typing import MutableMapping


def eprint(*args, sep=' ', end='\n', file=sys.stderr):
    """
    collect from: https://stackoverflow.com/questions/5574702/how-to-print-to-stderr-in-python
    """
    print(*args, sep=sep, end=end, file=file)


def override_str(clazz):
    """
    override default func __str__(), print Object like Java toString() style
    """

    def __str__(self):
        values: MutableMapping = {}
        for k, v in vars(self).items():
            if isinstance(v, list):
                values[k] = '[%s]' % ', '.join('%s' % item.__str__() for item in v)
            else:
                values[k] = v.__str__()

        return '%s(%s)' % (
            type(self).__name__,  # class name
            ', '.join('%s: %s' % item for item in values.items())
        )

    clazz.__str__ = __str__
    return clazz


class ShowProcess(object):
    """
    显示处理进度的类
    调用该类相关函数即可实现处理进度的显示
    # 效果为[>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>]100.00%
    """

    i = 0  # 当前的处理进度
    max_steps = 0  # 总共需要处理的次数
    max_arrow = 50  # 进度条的长度
    infoDone = 'done'

    def __init__(self, max_steps, infoDone='Done'):
        """
        初始化函数，需要知道总共的处理次数
        :param max_steps: 总共需要处理的次数
        :param infoDone: 结束时打印的字符
        """
        self.max_steps = max_steps
        self.i = 0
        self.infoDone = infoDone

    def show_process(self, i=None):
        """
        显示函数，根据当前的处理进度i显示进度
        :param i: 当前进度
        """
        if i is not None:
            self.i = i
        else:
            self.i += 1
        num_arrow = int(self.i * self.max_arrow / self.max_steps)  # 计算显示多少个'>'
        num_line = self.max_arrow - num_arrow  # 计算显示多少个'-'
        percent = self.i * 100.0 / self.max_steps  # 计算完成进度，格式为xx.xx%
        process_bar = '[' + '>' * num_arrow + '-' * num_line + ']' \
                      + '%.2f' % percent + '%' + '\r'  # 带输出的字符串，'\r'表示不换行回到最左边
        sys.stdout.write(process_bar)  # 这两句打印字符到终端
        sys.stdout.flush()
        if self.i >= self.max_steps:
            self.close()

    def close(self):
        print('')
        print(self.infoDone)
        self.i = 0


class RootPath(object):
    """获取根目录"""
    root_path = None

    def __init__(self):
        if RootPath.root_path == None:
            # 判断调试模式
            debug_vars = dict((a, b) for a, b in os.environ.items()
                              if a.find('IPYTHONENABLE') >= 0)

            # 根据不同场景获取根目录
            if len(debug_vars) > 0:
                """当前为debug运行时"""
                RootPath.root_path = sys.path[2]
            elif getattr(sys, 'frozen', False):
                """当前为exe运行时"""
                RootPath.root_path = os.getcwd()
            else:
                """正常执行"""
                RootPath.root_path = sys.path[1]

            # 替换斜杠
            RootPath.root_path = RootPath.root_path.replace('\\', '/')


def lookahead(iterable):
    """
    Pass through all values from the given iterable, augmented by the
    information if there are more values to come after the current one
    (True), or if it is the last value (False).
    collect from: https://stackoverflow.com/a/1630350
    >>>from selfusepy.utils import lookahead
    >>>from typing import List
    >>>c: List[int] = list()
    >>>for item, has_next in lookahead(c):
    >>>  if not has_next:
    >>>    # do something for last item
    >>>  # other item
    """
    # Get an iterator and pull the first value.
    it = iter(iterable)
    last = next(it)
    # Run the iterator to exhaustion (starting from the second value).
    for val in it:
        # Report the *previous* value (more to come).
        yield last, True
        last = val
    # Report the last value.
    yield last, False


def async_raise(tid, exctype):
    """Raises an exception in the threads with tid"""
    if not inspect.isclass(exctype):
        raise TypeError("Only types can be raised (not instances)")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid),
                                                     ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
        raise SystemError("PyThreadState_SetAsyncExc failed")
