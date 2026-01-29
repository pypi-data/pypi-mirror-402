import logging
import structlog
from typing import List, Any, Callable, Type, cast
from otel_declarative.Logging.logger_factory import LogConfig
from otel_declarative.constants import ObservabilityInternalNamespace
from otel_declarative.Infrastructure.async_log_engine import AsyncInfrastructureRegistry
from otel_declarative.Engines.log_processors import get_otel_context_injectors, get_field_renamer_processor
from otel_declarative.Models.Log.topology import ProcessorTopology, InjectionLayer, RenamingLayer, ProcessorChain
from otel_declarative.Models.Log.state import ReporterEngineState
from otel_declarative.Models.Log.context import LogContext, StructuredLogSettings
from otel_declarative.Models.Log.constants import LogFormat


class StructuredReporterFactory:
    """
    结构化日志工厂

    职责:
        1、配置编排: 聚合运行时配置、服务上下文与 OTel 处理器链
        2、引擎初始化: 负责 structlog 全局配置的原子化注入
        3、异步桥接: 协调 AsyncLogInfrastructure 构建非阻塞日志流水线
        4、记录器分发: 提供符合 structlog 协议的高性能记录器实例
    """
    def __init__(self, settings: StructuredLogSettings, log_context: LogContext, base_log_config: LogConfig):
        """
        :param settings: 结构化日志引擎全局设置模型
        :param log_context: 服务身份元数据上下文
        :param base_log_config: 基础日志配置
        """
        self._settings: StructuredLogSettings = settings
        self._log_context: LogContext = log_context
        self._base_config: LogConfig = base_log_config
        # 初始化引擎状态为 '待命' 快照, 消除离散布尔变量
        self._state: ReporterEngineState = ReporterEngineState.create_initial(_format=settings.log_format)

    def setup(self) -> None:
        """
        执行结构化日志系统的全量初始化流

        [Fix]
        逻辑:
            1、原子检查: 确保全局配置仅执行一次
            2、异步链路预热: 通过 AsyncInfrastructureRegistry 构建非阻塞的 QueueHandler
            3、2026.01.15 - 逻辑更改 - 流水线拆解与重组:
                - 分别获取上游组件 Context Injectors 与下游组件 Field Renamer
                - 调用 _build_full_processor_chain 执行拓扑排序, 解决 EventRenamer 竞争条件
            4、配置注入: 将完整的处理器链与物理异步 Sink 绑定至 structlog 全局单例
            5、状态切换: 原子替换引擎快照, 标记系统就绪
        """
        if self._state.is_ready:
            return

        # --- 1、构建底层异步 Handler (IoC 桥接 LoggerFactory) ---
        async_handler: logging.Handler = self._build_physical_async_sink()

        # --- 2、编排全链路观测处理器链 (基于分层容器模型) ---
        injection_layer: InjectionLayer = get_otel_context_injectors(field_mapping=self._settings.field_mapping, log_context=self._log_context)
        renaming_layer: RenamingLayer = get_field_renamer_processor(field_mapping=self._settings.field_mapping)
        topology = ProcessorTopology(injection_layer=injection_layer, renaming_layer=renaming_layer)
        final_chain: ProcessorChain = topology.to_chain()
        processor_list: List[Callable] = final_chain.unwrap()

        # --- 3、执行底层核心库配置注入 ---
        self._configure_structlog_core(processor_list, async_handler)

        # --- 4、原子替换状态快照, 确保线程安全 ---
        self._state = ReporterEngineState(
            is_ready=True,
            active_format=self._settings.log_format,
            processor_count=len(processor_list),
            has_async_infra=self._settings.enable_async
        )

    def get_logger(self, name: str = "otel.declarative") -> structlog.BoundLogger:
        """
        获取一个预配置完成的结构化记录器实例

        提供 Fail-safe 保护: 若引擎未就绪, 将自动触发引导流

        :parma name: 记录器逻辑名称, 用于在日志中标识模块
        :return: 具备异步能力, 携带 TraceID 与服务元数据的 structlog 记录器
        """
        if not self._state.is_ready:
            self.setup()

        root_ns = ObservabilityInternalNamespace.DEFAULT_LAYER.value
        if not name.startswith(root_ns):
            namespaced_name = f"{root_ns}.{name}"
        else:
            namespaced_name = name
        return structlog.get_logger(namespaced_name)

    @property
    def state(self) -> ReporterEngineState:
        """
        暴露当前引擎的只读运行状态快照

        :return: ReporterEngineState 实例
        """
        return self._state

    # --- 内部组件编排逻辑 ---

    def _build_physical_async_sink(self) -> logging.Handler:
        """
        协调异步基础设置管理器构建非阻塞输出句柄

        :return: 配置完成的 QueueHandler 实例
        """
        infra_manager = AsyncInfrastructureRegistry.get_infrastructure(settings=self._settings, log_config=self._base_config)
        return infra_manager.build_async_handler()

    def _configure_structlog_core(self, processors: List[Callable], sink_handler: logging.Handler) -> None:
        """
        执行 structlog 全局单例的底层配置注入, 完成 stdlib logging 的桥接

        :param processors: 已排序并封装的处理器 Callable 列表
        :param sink_handler: 异步消费端 QueueHandler
        """
        # 1、获取并配置统一的业务根  Logger
        root_ns = ObservabilityInternalNamespace.DEFAULT_LAYER.value
        root_business_logger = logging.getLogger(root_ns)

        # 2、挂载异步 Sink
        root_business_logger.handlers.clear()
        root_business_logger.addHandler(sink_handler)

        # 3、实施隔离, 禁止向 root logger 冒泡
        root_business_logger.propagate = False
        root_business_logger.setLevel(logging.NOTSET)

        # 4、根据配置模型选择最终渲染器策略
        renderer: Callable = (
            structlog.processors.JSONRenderer() if self._settings.log_format == LogFormat.JSON
            else structlog.dev.ConsoleRenderer(colors=True)
        )

        # 3、解包处理器链并注入全局配置
        structlog.configure(
            processors=processors + [renderer],
            # 使用 stdlib 工厂，它会自动将 get_logger("A") 映射为 logging.getLogger("A")
            # 配合 get_logger 方法中的命名空间前缀注入，实现路由闭环
            logger_factory=structlog.stdlib.LoggerFactory(),
            # 消除协议不匹配警告:
            # 强转 stdlib.BoundLogger 以匹配 structlog 严格的 BindableLogger 协议
            wrapper_class=cast(Type[structlog.typing.BindableLogger], cast(Any, structlog.stdlib.BoundLogger)),
            cache_logger_on_first_use=True,
        )

    def __repr__(self) -> str:
        """
        提供可监测的工厂状态摘要
        """
        return str(self._state)