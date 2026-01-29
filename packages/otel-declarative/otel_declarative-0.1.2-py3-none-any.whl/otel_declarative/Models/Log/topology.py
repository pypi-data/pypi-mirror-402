import structlog.contextvars
from typing import Dict, Any, List, Callable
from pydantic import BaseModel, Field, ConfigDict
from otel_declarative.Models.Log.constants import ILogProcessor

#  --- 处理器拓扑模块 ---

class InjectionLayer(BaseModel):
    """
    上下文注入层容器模型

    职责:
        1、聚合封装: 包含所有负责向日志事件中产生新数据的处理器 (TraceID、ServiceMetadata 等)
        2、语义明确: 明确标识该层级仅负责数据增补, 不涉及键名修改或格式化
        3、接口隔离: 仅接受符合 InjectionLayer 协议的可调用对象
    """
    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True, # 允许 Pydantic 校验 Protocol 类型
    )

    processors: List[ILogProcessor] = Field(
        default_factory=list,
        description="负责产生新元数据的处理器序列"
    )

    def as_list(self) -> List[ILogProcessor]:
        """
        获取原始处理器列表以供 structlog 配置使用

        :return: 符合 structlog 协议的处理器列表
        """
        return self.processors

class RenamingLayer(BaseModel):
    """
    字段重命名层容器模型

    职责:
        1、单一封装: 包含负责最终 Schema 映射的处理器
        2、末端约束: 明确标识该层级应位于处理链的末端 (但在渲染之前)
    """
    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True, # 允许 Pydantic 校验 Protocol 类型
    )

    processor: ILogProcessor = Field(
        ...,
        description="负责执行 Schema 映射的处理器"
    )

    def as_list(self) -> List[ILogProcessor]:
        """
        获取包装为列表的处理器, 便于链式拼接

        :return: 包含单个处理器的列表
        """
        return [self.processor]

class BaseLayer(BaseModel):
    """
    基础处理层容器模型

    职责:
        1、预置标准库: 封装 structlog 核心的基础处理器 (Context, Timestamp, Level)
        2、顺序固化: 确保基础元数据的生成顺序不被干扰
    """
    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
    )

    # 使用私有属性存储实际处理器列表, 避免 Pydantic 序列化 lambda 或复杂对象时的潜在问题
    _processors: List[Callable] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    def as_list(self) -> List[Callable]:
        """
        获取基础处理器序列

        :return: 不可变的基础处理器列表
        """
        return list(self._processors)

class NormalizationLayer(BaseModel):
    """
    内容标准化层容器模型

    职责:
        1、格式统一: 将异常、位置参数等非结构化数据转化为标准字典键
        2、编码安全: 确保所有内容通过 Unicode 解码
        3、前置约束: 必须位于 RenamingLayer 前执行
    """
    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True
    )

    _processors: List[Callable] = [
        structlog.processors.format_exc_info,
        structlog.processors.EventRenamer("event"),
        structlog.processors.UnicodeDecoder()
    ]

    def as_list(self) -> List[Callable]:
        """
        获取标准化处理器序列

        :return: 不可变的标准化处理器列表
        """
        return list(self._processors)

class ProcessorTopology(BaseModel):
    """
    日志处理器拓扑结构模型

    职责:
        1、全链路编排: 将松散的处理器容器重构为具有严格时序语义的强类型拓扑对象
        2、层级隔离: 明确划分基础层、注入层、标准化层与重命名层的边界
        3、链条组装: 提供标准化的 to_chain() 方法生成最终执行序列
    """
    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True, # 允许 Pydantic 校验 Protocol 类型
    )

    # --- 基础层 (组合关系, 强拥有, 自动初始化) ---
    base_layer: BaseLayer = Field(
        default_factory=BaseLayer,
        description="产生时间戳与日志等级的基础层"
    )

    # --- 注入层 (聚合关系, 外部注入) ---
    injection_layer: InjectionLayer = Field(
        ...,
        description="负责注入 TraceID 与服务元数据的注入层"
    )

    # --- 标准化层 (组合关系, 强拥有, 自动初始化) ---
    normalization_layer: NormalizationLayer = Field(
        default_factory=NormalizationLayer,
        description="负责内容清洗与标准化的中间层"
    )

    # --- 重命名层 (聚合关系, 外部注入) ---
    renaming_layer: RenamingLayer = Field(
        ...,
        description="负责最终 Schema 映射的重命名层"
    )

    def to_chain(self) -> "ProcessorChain":
        """
        生成符合 structlog 协议的完整处理器链容器

        执行顺序 (Strict Order):
            1、Base: 准备上下文与元数据 (Time, Level)
            2、Injection: 注入业务追踪信息 (TraceID, Service)
            3、Normalization: 生成 event / exception 标准键
            4、Renaming: 执行最终字段映射

        :return: 封装后的 ProcessorChain 对象
        """
        chain: List[Callable[[Any, str, Dict[str, Any]], Dict[str, Any]]] = []

        # 按严格拓扑顺序拼接
        chain.extend(self.base_layer.as_list())
        chain.extend(self.injection_layer.as_list())
        chain.extend(self.normalization_layer.as_list())
        chain.extend(self.renaming_layer.as_list())

        return ProcessorChain(processors=chain)

class ProcessorChain(BaseModel):
    """
    处理器链最终产物容器模型

    职责:
        1、终态封装: 承载已完成所有拓扑排序与校验、可直接交付给 structlog 的处理器序列
        2、不可变契约: 确保交付给 structlog.configure 的是一个不可被后续逻辑篡改的原子对象
        3、类型安全: 明确标识该对象内包含的是符合 Callable[[...], Dict] 协议的处理器列表
    """
    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True
    )

    processors: List[Callable[[Any, str, Dict[str, Any]], Dict[str, Any]]] = Field(
        ...,
        description="已排序的处理器 Callable 列表",
    )

    def unwrap(self) -> List[Callable]:
        """
        解包获取原始处理器列表

        :return: structlog 原生处理器列表
        """
        return self.processors