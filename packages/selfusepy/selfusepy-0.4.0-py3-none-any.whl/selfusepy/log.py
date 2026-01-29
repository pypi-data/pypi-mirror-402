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
#   File Name : log.py
#   Repo: https://github.com/LuomingXu/selfusepy


"""
Python log 增强
"""

import logging
import sys
import time
from datetime import datetime, timedelta, timezone
from logging import handlers, LogRecord
from typing import List, Optional

from selfusepy.utils import RootPath


def __delta_base__(fmt, delta: int, timestamp):
    return datetime.fromtimestamp(timestamp, timezone(timedelta(hours=delta))).timetuple()


levels: list = [logging.NOTSET, logging.DEBUG, logging.INFO, logging.WARN, logging.ERROR, logging.FATAL]


class Logger(object):
    """
    日志类
    usage: log = Logger('error.log').logger OR log = Logger().logger
           log.info('info')
    """

    def __init__(self, filename=None, time_offset: int = None,
                 levelToStderr=logging.WARNING,
                 fmt='%(asctime)s-[%(levelname)s]-[%(process)d/%(thread)d]-[%(threadName)s] %(customPathname)50s(%(lineno)d): %(message)s',
                 **kwargs):
        """
        init
        :param filename: 储存日志的文件, 为None的话就是不储存日志到文件
        :param time_offset: log的时区, 默认为8(UTC+08:00)
        :param levelToStderr: 写入到stderr的log级别, 默认为warning
        :param fmt: 日志格式
        :param kwargs: 对应TimedRotatingFileHandler的参数
        when: 间隔的时间单位. S秒, M分, H小时, D天, W每星期(interval==0时代表星期一) midnight 每天凌晨
        backupCount: 备份文件的个数, 如果超过这个个数, 就会自动删除
        """
        # logging.Formatter.converter = time_offset
        self.logger = logging.Logger(filename)
        CustomFormatter.time_offset = time_offset if time_offset else 8
        formatter = CustomFormatter(fmt)
        self.logger.setLevel(logging.NOTSET)  # 设置日志级别为notset, 所有的log都可以打印出来
        for level in levels:  # 在warn级别之上使用stderr
            if level >= levelToStderr:
                sh = logging.StreamHandler(stream=sys.stderr)
            else:
                sh = logging.StreamHandler(stream=sys.stdout)
            sh.setLevel(level)
            sh.setFormatter(formatter)
            sh.addFilter(StreamHandlerFilter(level))
            self.logger.addHandler(sh)
        self.logger.addFilter(LoggerFilter())

        if filename is not None:
            """实例化TimedRotatingFileHandler"""
            if 'encoding' in kwargs.keys():
                th = handlers.TimedRotatingFileHandler(filename=filename, **kwargs)
            else:
                th = handlers.TimedRotatingFileHandler(filename=filename, encoding='utf-8', **kwargs)
            th.setFormatter(formatter)  # 设置文件里写入的格式
            self.logger.addHandler(th)


class CustomFormatter(logging.Formatter):
    time_offset = None

    def formatTime(self, record: LogRecord, datefmt: Optional[str] = ...) -> str:
        ct = __delta_base__(self, self.time_offset, record.created)
        if datefmt:
            s = time.strftime(datefmt, ct)
        else:
            t = time.strftime(self.default_time_format, ct)
            s = self.default_msec_format % (t, record.msecs)

        return s


class StreamHandlerFilter(logging.Filter):

    def __init__(self, level):
        self.level = level
        super().__init__()

    def filter(self, record: logging.LogRecord) -> int:
        """
        若是此StreamHandler的leve与Record的级别不一致, 则不显示
        :param record:
        :return:
        """
        if self.level == record.levelno:
            return True
        return False


class LoggerFilter(logging.Filter):

    def _s_len(self, l: List[str]):
        len: int = 0
        for item in l:
            len += item.__len__() + 1
        return len

    def _replace_underline(self, l: List[str]):
        for i, item in enumerate(l):
            l[i] = item.replace('_', '')

    def filter(self, record: logging.LogRecord):
        s = str(record.pathname).replace('\\', '/').replace(RootPath().root_path, '').replace('/', '.')[1:]
        l: List[str] = s.split('.')
        l.pop(l.__len__() - 1)  # 丢弃最后的文件扩展名'py'
        file_name = l.pop(l.__len__() - 1)
        self._replace_underline(l)  # 有些py文件以'_'开头, 需要删去, 才能取首字母
        i: int = 0
        while self._s_len(l) + file_name.__len__() + record.funcName.__len__() > 50:  # 如果超出了长度再进行缩减操作
            if i >= l.__len__():  # 实在太长了缩减不了, 就算了, 需要保证最后的文件名与函数名的完整
                break
            l[i] = l[i][0]
            i += 1

        l.append(file_name)
        l.append(record.funcName)

        record.customPathname = '.'.join('%s' % item for item in l)
        """
        不能在这边直接就修改
        >>> record.pathname = '.'.join('%s' % item for item in l)
        有可能后面的log依赖这个pathname, 那么这个pathname就被修改了, 
        而没有被系统重新赋予正确的pathname
        例如test.log包中的多层级__init__, 就会出现这种问题
        """
        return True
