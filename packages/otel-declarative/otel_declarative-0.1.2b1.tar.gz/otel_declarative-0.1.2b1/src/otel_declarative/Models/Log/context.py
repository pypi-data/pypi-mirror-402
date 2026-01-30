from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from otel_declarative.Models.Log.constants import LogFormat
from otel_declarative.Models.Log.mapping import LogFieldMapping

# --- 上下文与设置模块 ---

class LogContext(BaseModel):
    """
    结构化日志强制上下文模型

    职责:
        1、定义每一行日志必须携带的 '全链路追踪' 核心字段
        2、作为 OtelTraceContextProcessor 注入数据的强类型契约
    """
    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
    )

    trace_id: Optional[str] = Field(
        default=None,
        alias="trace_id",
        description="OpenTelemetry 全局追踪标识符",
    )

    span_id: Optional[str] = Field(
        default=None,
        alias="span_id",
        description="OpenTelemetry 当前跨度标识符"
    )

    service_name: str = Field(
        ...,
        alias="service",
        description="产生日志的服务 / 应用的唯一名称"
    )

    environment: str = Field(
        default="production",
        description="部署环境标识 (例如: development, production)"
    )

    node_name: Optional[str] = Field(
        default=None,
        description="逻辑节点或 Pod 名称"
    )


class StructuredLogSettings(BaseModel):
    """
    结构化日志引擎全局设置模型

    职责:
        1、封装所有影响 structlog 初始化与运行行为的参数
        2、解耦日志逻辑与底层 I/O 基础设施
    """
    model_config = ConfigDict(
        frozen=True,
        extra="ignore"
    )

    # --- 渲染控制 ---
    log_format: LogFormat = Field(
        default=LogFormat.JSON,
        description="日志渲染格式策略选择"
    )

    # --- 异步性能控制 ---
    enable_async: bool = Field(
        default=True,
        description="是否启用基于 QueueHandler 的异步写入引擎"
    )

    queue_size: int = Field(
        default=1000,
        ge=100,
        description="异步日志缓冲区队列容量上限"
    )

    # --- 上下文注入控制 ---
    inject_otel_context: bool = Field(
        default=True,
        description="是否自动调用处理器注入 TraceID 与 SpanID"
    )

    # --- 字段映射控制 ---
    # 允许在不修改代码的情况下, 动态映射 structlog 默认字段名
    # 例如: 将 'event' 映射为 'message' 以适配特定 ELK 索引
    field_mapping: LogFieldMapping = Field(
        default_factory=LogFieldMapping,
        description="结构化字段名重映射配置对象, 支持嵌套校验"
    )

    def to_structlog_processors_config(self) -> Dict[str, Any]:
        """
        将模型转换为 structlog 配置所需的字典快照

        :return: 包含关键开关的字典
        """
        return {
            "format": self.log_format.value,
            "async_enabled": self.enable_async,
            "mapping": self.field_mapping
        }
