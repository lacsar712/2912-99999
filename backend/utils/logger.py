"""
日志工具
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from config import Config


class Logger:
    """日志工具类"""

    _instance = None
    _logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._init_logger()
        return cls._instance

    @classmethod
    def _init_logger(cls):
        """初始化日志器"""
        cls._logger = logging.getLogger('data_management')
        cls._logger.setLevel(getattr(logging, Config.LOG_LEVEL))

        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        cls._logger.addHandler(console_handler)

        # 文件处理器
        log_dir = os.path.dirname(Config.LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        cls._logger.addHandler(file_handler)

    @classmethod
    def info(cls, message: str):
        """记录信息日志"""
        cls._logger.info(message)

    @classmethod
    def error(cls, message: str):
        """记录错误日志"""
        cls._logger.error(message)

    @classmethod
    def warning(cls, message: str):
        """记录警告日志"""
        cls._logger.warning(message)

    @classmethod
    def debug(cls, message: str):
        """记录调试日志"""
        cls._logger.debug(message)

    @classmethod
    def exception(cls, message: str):
        """记录异常日志"""
        cls._logger.exception(message)


# 全局日志实例
logger = Logger()


def log_request(request_data: dict, user_id: int = None):
    """记录请求日志"""
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'user_id': user_id,
        'request': request_data
    }
    logger.info(f"Request: {log_data}")


def log_response(response_data: dict, status_code: int):
    """记录响应日志"""
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'status_code': status_code,
        'response': response_data
    }
    logger.info(f"Response: {log_data}")
