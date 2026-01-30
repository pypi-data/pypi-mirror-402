from dataclasses import dataclass
from typing import Optional
from otel_declarative.settings import ObservabilitySettings
from otel_declarative.Logging.logger_factory import LogConfig
from otel_declarative.provider import ObservabilityProvider

@dataclass(frozen=True)
class GlobalDependencyContainer:
    """
    全局依赖容器

    职责:
        1、状态持有: 集中管理观测引擎运行所需的所有单例组件
        2、不可变性: 采用 frozen=True, 确保容器一旦初始化, 其内部引用在当前生命周期内不可修改, 保证线程安全
        3、原子性: 将多个离散的观测组件聚合为单一原子状态, 消除系统中散落的全局变量
        4、解耦: 核心组件不感知容器的存在, 容器仅作为引导层的存储实体
    """
    # --- 核心配置快照 ---
    # 观测性全局设置模型
    settings: Optional[ObservabilitySettings] = None
    # 基础日志配置模型
    log_config: Optional[LogConfig] = None

    # --- 核心引擎组件 ---
    # 核心观测提供者实例
    provider: Optional[ObservabilityProvider] = None

    # --- 运行状态标识 ---
    # 原子布尔状态
    is_initialized: bool = False

    def __post_init__(self) -> None:
        """
        数据一致性后验逻辑

        在 dataclass 实例化完成后自动触发, 用于确保 is_initialized 为 True 时关键配置对象不为空
        """
        if self.is_initialized:
            if self.settings is None or self.log_config is None:
                raise ValueError("GlobalDependencyContainer 状态异常: 容器已标记为就绪, 但核心配置对象为空")

    def __repr__(self) -> str:
        """
        提供标准化的容器运行状态快照描述

        :return: 包含就绪状态与服务标识的描述字符串
        """
        status: str = "INITIALIZED" if self.is_initialized else "PENDING"
        service: str = self.settings.service_name if self.settings else "unknown"
        return (
            f"<GlobalDependencyContainer status={status} service={service} has_provider={self.provider is not None}>"
        )