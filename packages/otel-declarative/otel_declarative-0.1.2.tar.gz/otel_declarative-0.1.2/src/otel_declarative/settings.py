import os
import logging
from typing import Optional, List, Dict
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, BaseModel, ConfigDict
from otel_declarative.constants import OtelProtocol, OtelSecurityMode

class OtelExporterSettings(BaseModel):
    """
    OpenTelemetry 导出器专用子模型

    职责:
        1、封装 OTLP 导出相关的传输协议、端点与安全配置
        2、集中管理 TLS 证书路径等敏感信息
    """
    model_config = ConfigDict(frozen=True)

    endpoint: str = Field(
        default="http://otel-collector.monitoring:4317",
        description="OTLP Collector 的接受端点"
    )

    protocol: OtelProtocol = Field(
        default=OtelProtocol.GRPC,
        description="传输协议类型: grpc 或 http"
    )

    security_mode: OtelSecurityMode = Field(
        default=OtelSecurityMode.INSECURE,
        description="传输安全模式: insecure 或 tls"
    )

    # --- TLS 专用配置 ---
    ca_certificate_path: Optional[str] = Field(
        default=None,
        description="CA 根证书路径, 若开启 TLS 且该值为空, 则使用系统默认 CA 束"
    )

    client_key_path: Optional[str] = Field(
        default=None,
        description="客户端证书路径 (双向 TLS 认证专用)"
    )

    # --- OTLP 自定义 Header 支持 ---
    headers: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="OTLP 导出器自定义 HTTP Header, 常用于鉴权 (如: {'Authorization': 'Bearer token'})"
    )

class ObservabilitySettings(BaseSettings):
    """
    观测性全局配置对象

    职责:
        1、定义 OpenTelemetry 的基础导出参数
        2、定义性能判定阈值与采样策略
        3、定义声明式映射规则文件的存储路径
    """
    # --- 基础配置 ---
    enable_tracing: bool = Field(
        default=True,
        description="全链路追踪全局开关。设置为 False 时，装饰器将进入透传模式，不产生任何 Span 或属性"
    )
    service_name: str = Field(
        default="deepstream-worker-sidecar",
        description="向 OpenTelemetry 注册的服务唯一标识"
    )

    # --- 性能判定与采样策略 ---
    slow_query_threshold: float = Field(
        default=0.5,
        ge=0.0,
        description="慢查询判定阈值 (s), 当执行耗时超过该值时, TraceStatus 将被标记为 SLOW"
    )
    sampling_rate: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="追踪采样率 (0.0 - 1.0), 针对高频元数据路径, 适当调低以优化 CPU/IO"
    )

    # --- 策略化提取引擎注册表 ---
    mapping_config_path: str = Field(
        default="config/observability_mapping.yaml",
        description="存储声明式观测数据提取映射规则的 YAML 配置文件路径"
    )

    otel: OtelExporterSettings = Field(
        default_factory=OtelExporterSettings,
        description="OpenTelemetry 传输层详细设置"
    )

    # --- 第三方专业库集成配置 ---
    enable_dateparser: bool = Field(
        default=True,
        description="是否启用 dateparser 增强时间戳解析能力"
    )

    enable_humanize: bool = Field(
        default=True,
        description="是否启用 humanize 实现日志数据的可读化转换"
    )

    use_glom_spec: bool = Field(
        default=True,
        description="是否允许在转换阶段使用 glom 声明式结构转换"
    )

    # 默认时间时区配置
    default_timezone: str = Field(
        default="UTC",
        description="解析模糊时间字符串时的默认时区"
    )

    # 模型扫描路径配置
    model_scan_paths: List[str] = Field(
        default=["Core.Infrastructure.otel_declarative.Models"],
        description="解析引擎启动时应自动扫描并注册模型的模块路径列表"
    )

    # --- 配置模型行为定义 ---
    model_config = SettingsConfigDict(
        env_prefix="OBS_",
        case_sensitive=False,
        frozen=True,
        extra="ignore"
    )

    @field_validator("mapping_config_path")
    @classmethod
    def validate_mapping_file_exists(cls, v: str) -> str:
        """
        验证器: 确保声明式映射配置文件在本地文件系统中真实存在

        :param v: 验证后的文件路径字符串
        :return: 验证后的路径字符串
        """
        if not os.path.isabs(v):
            logging.warning(
                f"[otel_declarative Config] 映射规则路径 '{v}' 不是绝对路径"
                f"在高动态环境 (如 K8S) 下建议使用绝对路径以避免环境歧义"
            )

        if not os.path.exists(v):
            logging.warning(
                f"[otel_declarative Config] 映射规则文件未找到: '{v}'"
                f"观测引擎将切换至 '零规则' 模式, 仅记录基础 Span 属性"
            )

        return v