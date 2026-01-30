import dataclasses
from typing import Optional
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict
from otel_declarative.Logging.logger_factory import LogConfig, LogLevel, RotationType
from otel_declarative.Models.Log.context import LogContext, StructuredLogSettings
from otel_declarative.Models.Log.constants import LogFormat
from otel_declarative.Models.Log.mapping import LogFieldMapping

class LogEnvAdapter(BaseSettings):
    """
    日志环境适配器

    职责:
        1、声明式环境嗅探: 自动加载以 'LOG_' 为前缀的环境变量
        2、类型安全验证: 利用 Pydantic 引擎执行环境变量到强类型的转换
        3、影子模型桥接: 作为适配器, 将验证后的环境数据导出为核心组件所需的 LogConfig 实例
    """
    # --- 配置元数据 ---
    model_config = SettingsConfigDict(
        env_prefix='LOG_',
        case_sensitive=False,
        frozen=True,
        extra="ignore",
        # 允许通过非前缀的环境变量作为候选 (如同时支持 LOG_ENV 和 ENV)
        env_ignore_empty=True
    )

    # --- 基础标识映射 ---
    service_name: str = Field(
        default="deepstream-service",
        description="向日志系统注册的服务标识名"
    )
    environment: str = Field(
        default='production',
        validation_alias=AliasChoices("LOG_ENV", "ENV"),
        description="运行环境标识"
    )
    node_name: str = Field(
        default="unknown-node",
        validation_alias=AliasChoices("LOG_HOSTNAME", "HOSTNAME"),
        description="物理节点活容器 Pod 名称"
    )

    # --- 输出开关控制 ---
    level: LogLevel = Field(
        default=LogLevel.INFO,
        description="日志过滤等级 (DEBUG/INFO/WARNING/ERROR)"
    )
    enable_console: bool = Field(
        default=True,
        description="是否激活控制台标准输出"
    )
    enable_file: bool = Field(
        default=True,
        description="是否激活本地文件持久化"
    )

    # --- 异步性能控制 ---
    enable_async: bool = Field(
        default=True,
        description="是否启用异步日志队列"
    )
    queue_size: int = Field(
        default=1000,
        description="异步队列容量"
    )

    # --- 存储路径映射 ---
    log_dir: str = Field(
        default="/var/log/app",
        description="日志文件存储的绝对路径"
    )
    file_name: Optional[str] = Field(
        default=None,
        description="日志文件名, 若为空则由 service_name 生成"
    )

    # --- 轮转策略映射 ---
    rotation_type: RotationType = Field(
        default=RotationType.SIZE,
        description="日志切割模式: none, size, time"
    )
    max_bytes: int = Field(
        default=10 * 1024 * 1024,
        description="SIZE 模式下单文件最大字节数"
    )
    backup_count: int = Field(
        default=5,
        description="保留的历史归档文件数量"
    )
    when: str = Field(
        default="midnight",
        description="TIME 模式下的轮转时间单位"
    )
    interval: int = Field(
        default=1,
        description="TIME 模式下的时间间隔值"
    )
    utc: bool = Field(
        default=False,
        description="执行轮转时是否使用协调世界时"
    )

    # --- 格式化映射 ---
    format_string: str = Field(
        default="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        description="标准 logging 格式串"
    )

    # -- 结构化日志特有设置 ---
    log_format: LogFormat = Field(
        default=LogFormat.JSON,
        description="结构化渲染格式"
    )
    field_mapping: LogFieldMapping = Field(
        default_factory=LogFieldMapping,
        description="日志字段重映射配置"
    )

    # --- 核心导出方法 ---
    def to_log_config(self) -> LogConfig:
        """
        导出为核心组件 LogConfig 对象

        职责:
            实现从 Pydantic 模型到 Legacy Dataclass 的原子化转换
            利用 model_dump 确保所有环境数据已通过校验并按正确类型注入

        :return: 预填充了环境变量数据的 LogConfig 实例
        """
        log_config_fields = {f.name for f in dataclasses.fields(LogConfig)}
        filtered_data = {
            k: v for k, v in self.model_dump().items() if k in log_config_fields
        }
        return LogConfig(**filtered_data)

    def to_log_context(self) -> LogContext:
        """
        导出为结构化日志上下文模型

        :return: 已初始化的 LogContext 实例
        """
        return LogContext(service=self.service_name, environment=self.environment, node_name=self.node_name)

    def to_structured_settings(self) -> StructuredLogSettings:
        """
        导出为结构化日志引擎策略模型

        :return: 已初始化的 StructuredLogSettings 实例
        """
        return StructuredLogSettings(log_format=self.log_format, enable_async=self.enable_async, queue_size=self.queue_size, field_mapping=self.field_mapping)

    def __repr__(self) -> str:
        """
        状态描述增强
        """
        return f"<LogEnvAdapter service={self.service_name} level={self.level.value} file_mode={self.rotation_type.value}>"