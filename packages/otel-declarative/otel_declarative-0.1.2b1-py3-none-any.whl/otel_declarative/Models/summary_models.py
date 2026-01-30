from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict

class BaseSummary(BaseModel):
    """
    观测摘要基础模型

    职责:
        1、为所有派生的摘要 DTO 提供统一的 Pydantic 配置
        2、强制执行不可变性, 确保观测数据在传递过程中不被篡改
        3、支持别名映射和前向兼容性
    """
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore", # 忽略解析过程中可能多出的冗余字段
        frozen=True
    )

    def to_otel_attributes(self, prefix: str) -> Dict[str, Any]:
        """
        将模型数据转换为符合 OpenTelemetry 规范的扁平化属性字典

        逻辑:
            1、将模型序列化为原始字典
            2、过滤所有 None 值, 避免在 Span 中产生空属性
            3、为所有键名增加标准化的命名空间前缀

        :param prefix: 属性命名空间前缀
        :return: 经过前缀化处理的扁平化字典
        """
        raw_data = self.model_dump(exclude_none=True)
        return {f"{prefix}{k}": v for k, v in raw_data.items()}

class InputSummary(BaseSummary):
    """
    输入载体标准化摘要模型

    职责:
        1、承载从业务函数入口提取出的关键上下文
        2、对应 OTel Span 的初始属性集
    """
    # 业务协议标识
    command: Optional[str] = Field(
        default=None,
        description="业务通信协议定义的标准命令字"
    )
    # 业务唯一标识
    stream_id: Optional[str] = Field(
        default=None,
        description="跨系统流转的唯一业务流标识符"
    )
    # 来源节点标识
    pod_name: str = Field(
        ...,
        description="产生该观测数据的 K8s 计算节点名称",
        min_length=1
    )
    # 数据载体名称
    payload_type: str = Field(
        default="Unknown",
        description="运行时探测到的数据负载 Python 类型名称"
    )

    def to_otel_attributes(self, prefix: str = "input.") -> Dict[str, Any]:
        """
        重写父类方法, 锁定 'input.' 前缀语义

        :param prefix: 默认为 'input.'
        :return: 符合 OTel 规范的输入属性集
        """
        return super().to_otel_attributes(prefix)

class OutputSummary(BaseSummary):
    """
    输出结果标准化摘要模型

    职责:
        1、承载业务逻辑处理完成后的反馈元数据
        2、对应 OTel Span 结束前的状态补充属性
    """
    # 消息追踪锚点
    message_sha: Optional[str] = Field(
        default=None,
        description="由边车生成的全局唯一消息哈希, 用于全链路 ID 锚定"
    )
    # 处理结果简述
    result_brief: str = Field(
        default="No detail provided",
        description="处理结果的简要描述性信息"
    )
    # 转发状态标识
    is_forwarded: bool = Field(
        default=False,
        description="标识该业务消息是否已成功转发至下游服务"
    )

    def to_otel_attributes(self, prefix: str = "output.") -> Dict[str, Any]:
        """
        重写父类方法, 锁定 'output.' 前缀语义

        :param prefix: 默认为 'output.'
        :return: 符合 OTel 规范的输出属性集
        """
        return super().to_otel_attributes(prefix)
