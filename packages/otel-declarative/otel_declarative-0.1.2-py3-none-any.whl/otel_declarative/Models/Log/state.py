from pydantic import BaseModel, ConfigDict, Field
from otel_declarative.Models.Log.constants import LogFormat

# --- 引擎状态模块 ---

class ReporterEngineState(BaseModel):
    """
    结构化记录器引擎运行状态快照模型

    职责:
        1、状态聚合: 封装工厂在不同生命周期阶段的关键运行元数据
        2、线程安全: 利用 frozen=True 确保快照在读取过程中不可修改
        3、可观测性: 提供标准 __repr__ 实现, 集中暴露引擎健康度
    """
    model_config = ConfigDict(
        frozen=True,
    )

    # --- 核心状态属性 ---
    is_ready: bool = Field(
        default=False,
        description="就绪状态标识"
    )

    active_format: LogFormat = Field(
        default=LogFormat.JSON,
        description="当前日志渲染格式"
    )

    # 逻辑处理器链的长度 (可用于一致性审计)
    processor_count: int = Field(
        default=0,
        description="已挂载处理器数量"
    )

    has_async_infra: bool = Field(
        default=False,
        description="是否开启异步写入"
    )

    def __repr__(self) -> str:
        """
        提供标准化的状态监测输出
        """
        status: str = "READY" if self.is_ready else "PENDING"
        async_flag: str = "ASYNC" if self.has_async_infra else "SYNC"
        return (
            f"<ReporterEngineState status={status}, format={self.active_format.value}, mode={async_flag}, procs={self.processor_count}>"
        )

    @classmethod
    def create_initial(cls, _format: LogFormat) -> "ReporterEngineState":
        """
        构造初始待命状态

        :param _format: 当前系统配置中预设的日志渲染格式
        :return: 处于未就绪状态的 ReporterEngineState 实例
        """
        return cls(is_ready=False, active_format=_format)
