import os
import logging
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from enum import Enum
from typing import Optional
from dataclasses import dataclass

class LogLevel(Enum):
    """
    日志级别枚举
    """
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    def to_logging_level(self) -> int:
        return logging.getLevelName(self.value)

class RotationType(str, Enum):
    """
    日志轮转策略枚举
    """
    # 不输出到文件
    NONE = "none"
    # 按文件大小轮转
    SIZE = "size"
    # 按时间间隔轮转
    TIME = "time"

@dataclass
class LogConfig:
    """
    日志系统配置类
    """
    # --- 基础标识 ---
    service_name: str

    # --- 输出控制 ---
    level: LogLevel = LogLevel.INFO
    # 是否输出到标准输出
    enable_console: bool = True
    # 是否输出到文件
    enable_file: bool = True

    # --- 文件路径配置 (仅当 enable_file = True 时生效)
    log_dir: str = "/var/log/app"
    file_name: Optional[str] = None

    # --- 轮转策略配置 ---
    rotation_type: RotationType = RotationType.NONE

    # Size 策略参数
    max_bytes: int = 10 * 1024 * 1024
    backup_count: int = 5

    # Time 策略参数
    # S: Seconds, M: Minutes, H: Hours, D: Days, midnight: roll over at midnight
    when: str = "midnight"
    interval: int = 1
    # 是否使用 UTC 时间
    utc: bool = False

    # --- 格式配置 ---
    # 默认格式串，可由配置文件覆盖
    format_string: str = (
        "%(asctime)s | %(levelname)-8s | %(name)s | "
        "thread:%(thread)d | %(filename)s:%(lineno)d | %(message)s"
    )

    def get_log_file_path(self) -> str:
        """
        计算完整的日志文件绝对路径
        """
        fname = self.file_name or f"{self.service_name}.log"
        return os.path.join(self.log_dir, fname)

class LoggerFactory:
    """
    日志工厂类
    负责根据传入的配置对象构建和组装标准化的 Logger 实例
    """
    @staticmethod
    def setup_logger(config: LogConfig) -> logging.Logger:
        """
        根据配置文件初始化并获得 Logger 实例

        :param config: 完整的日志配置对象
        :return: 配置完成的 Logger
        """
        # --- 1、获取 Logger 对象 ---
        logger = logging.getLogger(config.service_name)
        logger.setLevel(config.level.to_logging_level())

        # 屏蔽第三方库的底层详细日志
        silenced_loggers = [
            "httpcore", "httpx", "hpack", "anyio",
            "httpcore._trace", "httpcore._client"
        ]
        for logger_name in silenced_loggers:
            logging.getLogger(logger_name).setLevel(logging.WARNING)

        # 清除已有的处理器
        if logger.handlers:
            logger.handlers.clear()

        # 防止日志传播到根记录器导致双重打印
        logger.propagate = False

        # --- 2、创建统一格式化器 ---
        formatter = logging.Formatter(config.format_string)

        # --- 3、配置控制太处理器 ---
        if config.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # --- 4、配置从文件处理器 ---
        if config.enable_file and config.rotation_type != RotationType.NONE:
            file_handler = LoggerFactory._create_file_handler(config)
            if file_handler:
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)

        return logger

    @staticmethod
    def _create_file_handler(config: LogConfig) -> Optional[logging.Handler]:
        """
        根据 RotationType 创建相应的文件处理器

        :param config: 日志系统配置对象
        """
        # --- 1、前置检查: 确保目录存在 ---
        if not os.path.exists(config.log_dir):
            try:
                os.makedirs(config.log_dir, exist_ok=True)
            except OSError as e:
                sys.stderr.write(f"CRITICAL: Logger 创建日志目录 {config.log_dir} 失败: {e}\n")
                return None

        file_path = config.get_log_file_path()

        try:
            handler: logging.Handler

            if config.rotation_type == RotationType.SIZE:
                # 按大小切割
                handler = RotatingFileHandler(
                    filename=file_path,
                    mode="a",
                    maxBytes=config.max_bytes,
                    backupCount=config.backup_count,
                    encoding="utf-8",
                    delay=True # 延迟打开文件, 直到第一条日志写入
                )
            elif config.rotation_type == RotationType.TIME:
                # 按时间切割
                handler = TimedRotatingFileHandler(
                    filename=file_path,
                    when=config.when,
                    interval=config.interval,
                    backupCount=config.backup_count,
                    encoding="utf-8",
                    utc=config.utc,
                    delay=True
                )
            else:
                return None
        except Exception as e:
            sys.stderr.write(f"CRICTL: 初始化文件 {file_path} 的文件句柄失败: {e}\n")
            return None

def get_child_logger(parent_logger_name: str, child_suffix: str) -> logging.Logger:
    """
    获取子模块 Logger 的辅助函数

    :param parent_logger_name: 父 Logger 名称 (例如 backfill)
    :param child_suffix: 子模块后缀 (例如 controllers.job)
    :return: 名称为 backfill.controllers.job 的 Logger
    """
    return logging.getLogger(f"{parent_logger_name}.{child_suffix}")