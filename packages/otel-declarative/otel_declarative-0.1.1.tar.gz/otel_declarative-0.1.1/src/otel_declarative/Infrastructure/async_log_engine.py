import queue
import logging
import atexit
import threading
from logging.handlers import QueueHandler, QueueListener
from typing import List, Optional, Dict, ClassVar
from otel_declarative.Models.Log.context import StructuredLogSettings
from otel_declarative.Logging.logger_factory import LoggerFactory, LogConfig
from otel_declarative.Infrastructure.handlers import NonBlockingQueueHandler

class AsyncLogInfrastructure:
    """
    异步日志基础设施管理器

    职责:
        1、核心队列维护: 负责初始化线程安全的高性能 Queue 对象, 缓冲业务侧高频产生的日志事件
        2、监听器生命周期管理: 管理后台 QueueListener 线程的启动与停机, 确保资源安全回收
        3、同步 Sink 桥接: 利用 LoggerFactory 构造底层物理输出层, 并将其封装为异步消费端
    """

    def __init__(self, settings: StructuredLogSettings, base_log_config: LogConfig):
        """
        :param settings: 结构化日志引擎全局配置模型
        :param base_log_config: 基础日志配置对象
        """
        self._settings = settings
        self._base_config: LogConfig = base_log_config
        # 内部状态
        self._queue: Optional[queue.Queue] = None
        self._listener: Optional[QueueListener] = None
        self._handler: Optional[QueueHandler] = None
        self._is_active: bool = False

    def build_async_handler(self) -> logging.Handler:
        """
        构建并启动异步日志处理流水线

        逻辑:
            1、调用 LoggerFactory 构造底层的物理输出 Handler 集合
            2、初始化线程安全的消息队列
            3、启动后台 QueueListener 线程执行日志的物理落盘
            4、向系统注册 atexit 钩子, 确保进程推出前强制刷新缓冲区

        :return: 配置完成的 QueueHandler 实例, 用于挂载至 stdlib logging 节点
        """
        # --- 1、构造物理输出层 ---
        sink_bridge_logger: logging.Logger = LoggerFactory.setup_logger(self._base_config)
        physical_handlers: List[logging.Handler] = sink_bridge_logger.handlers
        if not physical_handlers:
            # 若配置未开启任何输出, 返回 NullHandler 防止系统崩溃
            return logging.NullHandler()

        # --- 2、初始化异步队列 (队列深度由 StructureLogSettings 驱动) ---
        self._queue = queue.Queue(maxsize=self._settings.queue_size)

        # --- 3、构造并启动后台监听器 ---
        # respect_handler_level=True 确保物理 Handler 的 Level 设置生效
        self._listener = QueueListener(self._queue, *physical_handlers, respect_handler_level=True)
        self._listener.start()
        self._is_active = True

        # --- 4、注册进程退出清理机制 ---
        atexit.register(self.shutdown)

        # --- 5、构造前端入队处理器
        self._handler = NonBlockingQueueHandler(self._queue)

        # [Fix 2026.01.15]
        return self._handler

    def shutdown(self) -> None:
        """
        停止后台监听线程并确保队列中积压的日志记录完成最终分发

        Fail-safe 机制:
            1、优先尝试正常的 stop() 发送哨兵
            2、若队列已满导致 Full 异常, 主动执行退避策略
                - 丢弃最旧的日志以腾出空间
                - 再次尝试发送哨兵
            3、确保在极端积压场景下也能优雅退出, 避免阻塞主进程
        """
        if not (self._listener and self._is_active):
            return

        if getattr(self._listener, "_thread", None) is None:
            self._is_active = False
            return

        try:
            self._listener.stop()
        except queue.Full:
            max_retries: int = 3
            for _ in range(max_retries):
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    pass

                try:
                    if getattr(self._listener, "_thread", None) is None:
                        break
                    self._listener.stop()
                    break
                except queue.Full:
                    # 依然满 (高并发写入竞争), 继续重试
                    continue
            else:
                pass
        except AttributeError:
            # 处理 _thread 为 None 的情况
            pass

        self._is_active = False

    @property
    def is_running(self) -> bool:
        """
        获取当前异步基础设施的运行状态标识
        """
        return self._is_active

class AsyncInfrastructureRegistry:
    """
    异步基础设施注册中心

    职责:
        1、单例控制: 确保每个 LogConfig 对应的异步管理器在全局范围内唯一
        2、Fail-safe 访问: 提供安全的管理器获取入口, 封装初始化复杂度
    """
    # 全局单例注册表
    _managers: Dict[str, AsyncLogInfrastructure] = {}
    # 线程同步原语: 可重入锁
    _lock: ClassVar[threading.RLock] = threading.RLock()

    @classmethod
    def get_infrastructure(cls, settings: StructuredLogSettings, log_config: LogConfig) -> AsyncLogInfrastructure:
        """
        根据配置标识获取或创建异步基础设施管理器

        逻辑:
            1、无锁读取
            2、仅在实例不存在时竞争锁
            3、获取锁后再次检查, 防止重复初始化
            4、安全执行带有副作用的初始化逻辑

        :param settings: 结构化日志设施
        :param log_config: 基础日志配置
        :return: 活跃且唯一的 AsyncLogInfrastructure 实例
        """
        # 使用服务名作为注册索引键
        registry_key: str = log_config.service_name

        if registry_key in cls._managers:
            return cls._managers[registry_key]

        with cls._lock:
            if registry_key not in cls._managers:
                instance = AsyncLogInfrastructure(
                    settings=settings,
                    base_log_config=log_config
                )
                cls._managers[registry_key] = instance

        return cls._managers[registry_key]