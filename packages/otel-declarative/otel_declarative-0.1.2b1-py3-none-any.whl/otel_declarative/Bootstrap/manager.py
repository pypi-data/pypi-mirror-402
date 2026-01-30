import threading
from typing import ClassVar, Optional
from otel_declarative.Bootstrap.container import GlobalDependencyContainer
from otel_declarative.Bootstrap.adapters import LogEnvAdapter
from otel_declarative.settings import ObservabilitySettings
from otel_declarative.Factories.extractor_factory import ExtractorFactory
from otel_declarative.Reporters.structured_reporter import StructuredReporterFactory
from otel_declarative.provider import ObservabilityProvider
from otel_declarative.Logging.logger_factory import get_child_logger

# 引导层专用记录器
_bootstrap_logger = get_child_logger("otel_declarative.Infrastructure", "BootstrapManager")

class BootstrapManager:
    """
    引导管理器

    职责:
        1、生命周期编排: 负责从环境嗅探到 Provider 实例化的全链路组装过程
        2、单例状态管理: 维护全局依赖容器的单例状态, 防止重复初始化
        3、依赖注入: 协调配置、工厂与提供者直接的对象图构建
        4、线程安全保护: 利用递归锁实现高并发环境下的原子初始化
    """
    # --- 类级别私有变量 ---
    _lock: ClassVar[threading.RLock] = threading.RLock()
    _container: ClassVar[Optional[GlobalDependencyContainer]] = None

    @classmethod
    def ensure_initialized(cls) -> GlobalDependencyContainer:
        """
        确保观测引擎容器已完成初始化

        :return: 处于活跃状态的全局依赖容器实例
        """
        if cls._container is None or not cls._container.is_initialized:
            with cls._lock:
                if cls._container is None or not cls._container.is_initialized:
                    cls._container = cls._perform_bootstrap()
        return cls._container

    @classmethod
    def _perform_bootstrap(cls) -> GlobalDependencyContainer:
        """
        执行核心引导流与组件装配流水线

        职责:
            1、触发配置嗅探: 实例化 ObservabilitySettings 与 LogEnvAdapter
            2、构建基础设施: 初始化提取工厂与结构化日志记录工厂
            3、装配提供者: 构造最终的 ObservabilitySettings
            4、封装快照: 生成不可变的全局依赖容器

        :return: 处于就绪状态的 GlobalDependencyContainer 实例
        """
        try:
            _bootstrap_logger.info("正在执行声明式观测引擎全量引导")

            # --- 配置加载 ---
            obs_settings: ObservabilitySettings = ObservabilitySettings()
            log_adapter: LogEnvAdapter = LogEnvAdapter()

            # --- 策略工厂引导 ---
            extractor_factory: ExtractorFactory = ExtractorFactory(settings=obs_settings)
            reporter_factory: StructuredReporterFactory = StructuredReporterFactory(
                settings=log_adapter.to_structured_settings(),
                log_context=log_adapter.to_log_context(),
                base_log_config=log_adapter.to_log_config()
            )
            reporter_factory.setup()

            # --- 观测提供者装配 ---
            provider: ObservabilityProvider = ObservabilityProvider(
                settings=obs_settings,
                extractor_factory=extractor_factory,
                reporter_factory=reporter_factory
            )

            # --- 锁定状态快照 ---
            global_dependency_container_obj = GlobalDependencyContainer(
                settings=obs_settings,
                log_config=log_adapter.to_log_config(),
                provider=provider,
                is_initialized=True
            )
            _bootstrap_logger.info(f"观测引擎引导完成 | 服务: {obs_settings.service_name} | 状态: {'Ready' if global_dependency_container_obj.is_initialized else 'NotReady'} | 追踪开关: {obs_settings.enable_tracing}")
            return global_dependency_container_obj
        except Exception as e:
            _bootstrap_logger.exception(f"观测引擎引导致命异常: {type(e).__name__} | 系统将自动降级至 'Null-Object' 安全透传模式")
            return GlobalDependencyContainer(is_initialized=False)

    @classmethod
    def get_container(cls) -> GlobalDependencyContainer:
        """
        获取当前容器的引用

        注: 若系统尚未引导, 将返回一个  is_initialized=False 的临时空快照

        :return: GlobalDependencyContainer 实例
        """
        if cls._container is None:
            return GlobalDependencyContainer(is_initialized=False)
        return cls._container

    @classmethod
    def reset(cls) -> None:
        """
        重置引导管理器单例, 仅用于单元测试活紧急热重载场景
        """
        with cls._lock:
            cls._container = None
            _bootstrap_logger.warning(f"观测引擎引导状态已重置")