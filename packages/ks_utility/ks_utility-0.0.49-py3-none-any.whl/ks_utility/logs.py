from datetime import datetime
import logging
import logging.handlers
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
from typing import Optional
from pathlib import Path
import inspect
import socket
from datetime import timezone

from .bases import Base
from .systems import mkdir

LEVEL2STR = {
    DEBUG: 'DEBUG',
    INFO: 'INFO',
    WARNING: 'WARNING',
    ERROR: 'ERROR',
    CRITICAL: 'CRITICAL'
}
STR2LEVEL = {
    'DEBUG': DEBUG,
    'INFO': INFO,
    'WARNING': WARNING,
    'ERROR': ERROR,
    'CRITICAL': CRITICAL
}
class Logger():
    # 如果要精确的日志不混淆，例如高频交易，需要吧file_fmt设置为'%Y%m%d_%H%M%S.%f' 毫秒级别
    def __init__(
        self,
        path: Optional[Path]=None,
        name: Optional[str]=None,
        file_fmt='%Y%m%d',
        fluent_service = 'fluent_service_not_set',
        fluent_host='',
        fluent_port=24224,
        fluent_tag='',
        fluent_label='',
        fluent_levels=[ERROR, CRITICAL]
    ):  
        self.fluent_service = fluent_service
        self.fluent_levels = fluent_levels
        self.fluent_label = fluent_label
        self.fluent_tag = fluent_tag or socket.gethostname()
        if fluent_host:
            from fluent import sender
            self.fluent = sender.FluentSender(
                tag=fluent_tag,
                host=fluent_host,
                port=fluent_port
            )
        else:
            self.fluent = None
        if not file_fmt:
            file_fmt = '%Y%m%d'
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO) # 指定被处理的信息级别为最低级DEBUG，低于level级别的信息将被忽略
        # 输出到file
        logger_name = name or 'ks_utility'
        logger_path: Path = path or Path.home().joinpath('.ks_logs').joinpath(logger_name)
        if isinstance(logger_path, str):
            logger_path = Path(logger_path)
        logger_path.mkdir(parents=True, exist_ok=True)
        file_name = '%s.log'%(datetime.now().strftime(file_fmt))
        file_path = logger_path.joinpath(file_name)
        fh = logging.handlers.RotatingFileHandler(file_path, mode='a', encoding='utf-8')  # 不拆分日志文件，a指追加模式,w为覆盖模式
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s: %(message)s"))

        logger = self.logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        if not logger.handlers:
            logger.addHandler(ch)
            logger.addHandler(fh)

    def debug(self, msg):
        self.logger.debug(msg)
        
    def info(self, msg):
        self.logger.info(msg)
        
    def warn(self, msg):
        self.logger.warning(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def exception(self, msg):
        self.logger.exception(msg)
        
    def error(self, msg):
        self.logger.error(msg)

    def log(self, msg='hello_log', tag=[], level=INFO, title=None, name=None, fn_level=1):
        if self.fluent and level in self.fluent_levels:
            fluent_label = '.'.join([self.fluent_label] + tag) or 'global'
            self.fluent.emit(fluent_label, {
                "host": socket.gethostname(),
                "level": LEVEL2STR[level].lower(),
                "environment": "prod",
                "service_name": self.fluent_service,
                "log": msg,
                "@timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            })
        if not title:
            if fn_level == 0:
                caller_frame  = inspect.currentframe()
            elif fn_level == 1:
                caller_frame  = inspect.currentframe().f_back
            elif fn_level == 2:
                caller_frame  = inspect.currentframe().f_back.f_back
            name = name or caller_frame.f_code.co_name

            title = f'[{self.__class__.__name__}.{name}:{caller_frame.f_lineno}]'
        content = f'{title}'

        if tag:
            if not isinstance(tag, list):
                tag = [tag]
            for tag_item in tag:
                if tag_item:
                    content += f'【{tag_item}】'
        content += str(msg)

        self.logger.log(msg=content, level=level)

# root_path = os.path.join(os.path.dirname(__file__), '..')

# 20240807去除base，因为pyside6的基类不一样，要多重继承需要有相同的基类
class LoggerBase():
    def __init__(
        self,
        path = None,
        name=None,
        file_fmt: str=None,
        fluent_host='',
        fluent_port=24224,
        fluent_tag='',
        fluent_levels=[ERROR, CRITICAL]
    ):
        self.logger_name = name or self.__class__.__name__
        self.file_fmt = file_fmt
        self.logger_path = path or Path.home().joinpath('.ks_logs').joinpath(self.logger_name) # 项目跟文件夹
        self.logger = Logger(
            path=self.logger_path,
            name=self.logger_name,
            file_fmt=self.file_fmt,
            fluent_host=fluent_host,
            fluent_port=fluent_port,
            fluent_tag=fluent_tag,
            fluent_levels=fluent_levels
        ) # 日志记录器
        
    def log(self, msg='hello_log', tag=[], level=INFO, title=None, name=None, fn_level=1):
        if not title:
            if fn_level == 0:
                caller_frame  = inspect.currentframe()
            elif fn_level == 1:
                caller_frame  = inspect.currentframe().f_back
            elif fn_level == 2:
                caller_frame  = inspect.currentframe().f_back.f_back
            name = name or caller_frame.f_code.co_name

            title = f'[{self.__class__.__name__}.{name}:{caller_frame.f_lineno}]'

        return self.logger.log(msg=msg, tag=tag, level=level, title=title, name=name, fn_level=fn_level)

    def update_logger(self):
        self.init_dir()
        self.logger = Logger(self.module_path)


