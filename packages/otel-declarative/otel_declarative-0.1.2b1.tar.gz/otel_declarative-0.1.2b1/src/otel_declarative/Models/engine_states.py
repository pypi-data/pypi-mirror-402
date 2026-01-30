from dataclasses import dataclass, field
from typing import Dict, Optional
from otel_declarative.Interfaces.extractor import IExtractor
from otel_declarative.Engines.model_registry import ModelRegistry
from otel_declarative.Engines.path_resolver import PathResolver
from otel_declarative.Engines.object_hydrator import ObjectHydrator

@dataclass(frozen=True)
class ObservabilityEngineState:
    """
    观测引擎状态快照容器

    职责:
        1、聚合强耦合组件: 将模型注册中心、解析引擎、装配引擎和提取器实例打包为单一原子单元
        2、支持无锁切换: 利用 python 的引用赋值原子性, 通过替换该容器实例实现无锁热重载
        3、保证数据一致性: 确保在任何时刻提取逻辑所使用的模型定义与路径解析逻辑是完全匹配的
    """
    # --- 核心引擎组件 ---
    model_registry: ModelRegistry = field(
        metadata={"description": "负责 DTO 模型类定义的动态检索与管理"}
    )

    object_hydrator: ObjectHydrator = field(
        metadata={"description": "负责将解析出的原始数据递归装配为强类型的 Pydantic 对象"}
    )

    path_resolver: PathResolver = field(
        metadata={"description": "负责基于 JMESPath 表达式在业务上下文中检索并转换数据"}
    )

    # --- 策略分发容器 ---
    extractors: Dict[str, IExtractor] = field(
        default_factory=dict,
        metadata={"description": "逻辑层级到具体提取器实例的映射表"}
    )

    # --- 运行状态标识 ---
    is_ready: bool = field(
        default=False,
        metadata={"description": "标识当前状态快照是否已完成初始化并可投入生产使用"}
    )

    def get_extractor_for_layer(self, layer: str) -> Optional[IExtractor]:
        """
        [读操作] 从当前快照中安全获取指定层级的提取器

        :param layer: 业务层级标识符
        :return: 对应的提取器实例
        """
        if not self.is_ready:
            return None

        return self.extractors.get(layer)

    @classmethod
    def create_empty(cls) -> 'ObservabilityEngineState':
        """
        构造一个处于未就绪状态的初始占位状态对象

        职责:
            1、为 ExtractorFactory 提供系统引导初期的 Null-Object 实例
            2、采样延迟导入方式加载引擎组件, 避免循环导入
            3、使用空对象实例填充必填字段, 确保系统在未就绪状态下调用属性时不触发 AttributeError
            4、锁定 is_ready = False, 令 get_extractor_for_layer 能够正常执行 fail-safe 拦截

        :return: 处于未就绪状态的 ObservabilityEngineState 实例
        """
        from otel_declarative.Engines.model_registry import ModelRegistry
        from otel_declarative.Engines.object_hydrator import ObjectHydrator
        from otel_declarative.Engines.path_resolver import PathResolver
        from otel_declarative.Engines.converter_registry import ConverterRegistry
        from otel_declarative.settings import ObservabilitySettings

        # 1、构造基础配置环境
        default_settings: ObservabilitySettings = ObservabilitySettings()
        # 2、构造底层空对象内核
        empty_model_reg: ModelRegistry = ModelRegistry()
        empty_conv_reg: ConverterRegistry = ConverterRegistry(default_settings)
        empty_hydrator: ObjectHydrator = ObjectHydrator(empty_model_reg)
        # 3、构造路径解析器占位符
        empty_resolver: PathResolver = PathResolver(
            converter_registry=empty_conv_reg,
            object_hydrator=empty_hydrator,
        )
        return cls(
            model_registry=empty_model_reg,
            object_hydrator=empty_hydrator,
            path_resolver=empty_resolver,
            extractors={},
            is_ready=False,
        )

    def __repr__(self) -> str:
        """
        提供可观测的调试信息

        :return: 描述当前快照状态的字符串
        """
        status: str = "READY" if self.is_ready else "NOT_READY"
        layers: list[str] = list(self.extractors.keys())
        return f"<ObservabilityEngineState status={status} active_layers={layers}>"

    def __post_init__(self) -> None:
        """
        数据一致性后验逻辑, 在 dataclass 实例化完成后自动触发 (由 PEP 557 定义)

        职责:
            1、验证核心引擎组件是否已注入
            2、在构造函数执行到最后一行, 即将返回实例时, 强制执行组件连通性检查

        :raises:
            TypeError - 当核心引擎组件类型不匹配时抛出
            ValueError - 当系统处于就绪状态单关键依赖缺失时抛出
        """
        required_components: list = [
            ("model_registry", self.model_registry),
            ("object_hydrator", self.object_hydrator),
            ("path_resolver", self.path_resolver),
        ]
        for name, component in required_components:
            if component is None:
                raise ValueError(f"ObservabilityEngineState 初始化失败: 核心组件 '{name}' 为空")

        if self.is_ready:
            if not isinstance(self.extractors, dict):
                raise TypeError("ObservabilityEngineState 就绪状态校验失败: 'extractors' 必须是 Dict 类型")

            if not self.extractors:
                from otel_declarative.Logging.logger_factory import get_child_logger
                _audit_logger = get_child_logger("otel_declarative.Audit", "EngineState")
                _audit_logger.warning(
                    f"[otel_declarative Audit] 观测引擎快照已就绪, 但 'extractors' 规则映射表为空"
                    f"系统将进入 '基础追踪模式'"
                    f"仅会产生标准 OpenTelemetry Span，将无法动态提取和注入业务相关的 Attributes"
                )
