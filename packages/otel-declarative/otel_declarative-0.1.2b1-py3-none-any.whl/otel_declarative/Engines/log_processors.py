import os
from typing import Any, Dict, List, Optional
from opentelemetry import trace
from otel_declarative.Models.Log.topology import InjectionLayer, RenamingLayer
from otel_declarative.Models.Log.context import LogContext
from otel_declarative.Models.Log.mapping import LogFieldMapping
from otel_declarative.Models.Log.constants import FieldContract, ILogProcessor


class OtelTraceContextProcessor:
    """
    OpenTelemetry 追踪上下文处理器

    职责:
        1、运行时提取: 从 OTel 全局上下文中动态挖取当前协程 / 线程活跃 Span 的 TraceID 与 SpanID
        2、结构化注入: 按照配置对象定义的 Key 名将追踪标识注入日志字典
        3、状态感知: 仅在存在有效活跃 Span 时执行注入, 否则保持事件字典完整性
    """
    def __init__(self, field_mapping: LogFieldMapping):
        """
        :param field_mapping: 字段重映射配置对象, 定义输出字典中的键名
        """
        self._mapping: LogFieldMapping = field_mapping

    def __call__(self, logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        structlog 处理器核心入口

        :param logger: 记录器实例
        :param method_name: 日志级别方法名
        :param event_dict: 当前待处理的日志事件字典
        :return: 注入了 Trace 上下文后的事件字典
        """
        span = trace.get_current_span()

        if span and span.get_span_context().is_valid:
            span_context = span.get_span_context()
            # 将 TraceID 和 SpanID 转换为标准 16 进制字符串
            '''
            1、在 OpenTelemetry Python SDK 的内部实现中, span_context.trace_id 和 span_context.span_id 是以 原始整数 (int) 形式存储的
            TraceID 是一个 128 位的整数, SpanID 是一个 64 位的整数
            如果直接将这些整数写入日志, 可观测性后端 (如 Jaeger, ELK, Grafana) 无法识别这种十进制格式，导致 '链路-日志' 关联失效
            2、根据 W3C Trace Context 规范和 OpenTelemetry 标准: Trace ID 必须表示为 32 个字符的十六进制字符串 (小写), Span ID 必须表示为 16 个字符的十六进制字符串 (小写)
            3、如果在此处将 TraceID 直接以 int 格式写入 JSON 日志, 在解析时会发生精度丢失, 导致日志中的 ID 变成一个近似值，从而彻底无法与追踪系统匹配
            '''
            event_dict.setdefault(self._mapping.trace_id, format(span_context.trace_id, "032x"))
            event_dict.setdefault(self._mapping.span_id, format(span_context.span_id, "016x"))
        return event_dict

class ServiceMetadataProcessor:
    """
    服务身份元数据处理器

    职责:
        1、注入静态标识: 将服务名、运行环境等核心标识注入每行日志, 实现分布式环境下的身份溯源
        2、K8S 现场捕获: 自动探测宿主 Pod 名称, 实现物理机与集群逻辑节点的关联
        3、强类型一致: 使用 LogContext 模型作为注入数据的契约
    """
    def __init__(self, log_context: LogContext, field_mapping: LogFieldMapping):
        """
        :param log_context: 包含服务身份信息的强类型上下文模型
        """
        self._context: LogContext = log_context
        self._mapping: LogFieldMapping = field_mapping
        self._pod_name: str = getattr(self._context, "node_name", None) or os.getenv("HOSTNAME") or "unknown-node"

    def __call__(self, logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 structlog 的事件字典的元数据注入流水线

        依据 structlog 处理器协议, 本方法在日志事件被渲染 / 输出前自动触发

        负载将该服务实例的身份信息注入到事件上下文

        :param logger: 当前活跃的结构化记录器实例
        :param method_name: 触发日志生产的逻辑方法名称
        :param event_dict: 当前待处理的结构化事件字典
        :return: 经过元数据增强后的事件字典, 供流水线下游处理器继续处理
        """
        event_dict.setdefault(self._mapping.service, self._context.service_name)
        event_dict.setdefault(self._mapping.environment, self._context.environment)
        if self._pod_name:
            event_dict.setdefault(self._mapping.pod_name, self._pod_name)

        return event_dict

class LogFieldRenamer:
    """
    日志标准字段重命名处理器

    职责:
        1、动态 Schema 映射: 基于配置模型定义的字段字段执行键名转换, 实现系统内部 Schema 与外部存储 Schema 的解耦
        2、消除逻辑硬编码: 通过模型内省字段发现迁移目标
        3、零配置扩展性: 当 LogFieldMapping 模型新增字段定义时, 该处理器无需修改代码即可自动支持新字段的重命名
    """
    def __init__(self, field_mapping: LogFieldMapping):
        """
        :param field_mapping: 字段重映射配置对象
        """
        self._mapping: LogFieldMapping = field_mapping
        # 预计算动态迁移矩阵
        # 格式: {'原始库输出键名': '用户定义输出键名'}  
        self._migration_matrix: Dict[str, str] = {}
        # [Fix 2026.01.17]: PydanticDeprecatedSince211: Accessing the 'model_fields' attribute on the instance is deprecated.
        # 修复过时的 Pydantic v2 API 的使用方式
        # 原代码: for field_name, field_info in self._mapping.model_fields.items():
        for field_name, field_info in type(self._mapping).model_fields.items():
            # 查找该字段关联的 FieldContract 契约对象
            contract: Optional[FieldContract] = self._find_contract(field_info.metadata)
            # 仅处理明确声明了可重命名契约的字段
            if contract and contract.is_renamable and contract.source_key:
                target_key: str = getattr(self._mapping, field_name)
                if contract.source_key != target_key:
                    self._migration_matrix[contract.source_key] = target_key

    def __call__(self, logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行结构化日志字段的动态重命名映射

        逻辑:
            1、迭代预计算的迁移矩阵
            2、安全检查: 判定当前事件字典是否包含待迁移的源键
            3、原子操作: 利用 dict.pop 确保数据从旧键迁移到新键的过程不发生丢失

        :param logger: structlog 记录器实例
        :param method_name: 日志级别方法名
        :param event_dict: 待处理的结构化日志事件字典
        :return: 经过 Schema 映射转换后的事件字典
        """
        if not self._migration_matrix:
            return event_dict

        for source_key, target_key in self._migration_matrix.items():
            if source_key in event_dict:
                event_dict[target_key] = event_dict.pop(source_key)

        return event_dict

    def __repr__(self) -> str:
        """
        提供可调试的状态摘要
        """
        return f"<LogFieldRenamer matrix_size={len(self._migration_matrix)}>"

    def _find_contract(self, metadata: List[Any]) -> Optional[FieldContract]:
        """
        从 Pydantic 字段元数据列表中检索 FieldContract 实例

        :param metadata: Pydantic 字段的元数据列表
        :return: 找到的契约对象
        """
        for item in metadata:
            if isinstance(item, FieldContract):
                return item
        return None

def get_otel_context_injectors(field_mapping: LogFieldMapping, log_context: LogContext) -> InjectionLayer:
    """
    获取 OTel 上下文注入处理器链

    职责:
        1、构建仅负责生产数据的处理器链 (Trace Context、Service Metadata)
        2、作为 structlog 处理流水线的上游组件, 确保所有元数据在渲染前被注入
        3、依赖注入: 将强类型的映射配置与上下文契约注入具体的处理器实例
        4、利用 InjectionLayer 容器封装, 增强类型语义

    :param field_mapping: 定义输出字段键名的映射配置对象
    :param log_context: 包含服务身份信息的强类型上下文模型
    :return: 包含处理器序列的注入层容器对象
    """
    processors: List[ILogProcessor] = [
        OtelTraceContextProcessor(field_mapping=field_mapping),
        ServiceMetadataProcessor(log_context=log_context, field_mapping=field_mapping),
    ]
    return InjectionLayer(processors=processors)

def get_field_renamer_processor(field_mapping: LogFieldMapping) -> RenamingLayer:
    """
    获取字段重命名处理器工厂方法

    职责:
        1、构建仅负责修改键名的处理器
        2、作为 structlog 处理流水线的末端组件, 确保在 EventRenamer 与 ExceptionFormatter 之后执行
        3、隔离性: 独立于注入逻辑, 允许灵活调整其在处理器链中的拓扑位置
        4、利用 RenamingLayer 容器封装, 增强类型语义

    :param field_mapping: 包含 FieldContract 元数据契约的字段映射配置
    :return: 符合 structlog Processor 协议的字段重命名处理器实例
    """
    processor = LogFieldRenamer(field_mapping=field_mapping)
    return RenamingLayer(processor=processor)