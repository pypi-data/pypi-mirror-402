from typing import Any, Protocol, Type, Optional, runtime_checkable
from otel_declarative.Models.summary_models import InputSummary, OutputSummary

@runtime_checkable
class IExtractor(Protocol):
    """
    元数据提取器接口协议

    定义从原始业务载体中提取标准化观测摘要的标准行为
    """
    def extract_input(self, args: Any, kwargs: Any) -> InputSummary:
        """
        从被装饰函数的原始调用参数中提取标准化输入摘要

        职责:
            1、识别并解析 args / kwargs 中的业务载体
            2、负责防御性参数校验, 确保提取逻辑不会感染主业务流程
            3、构造并返回 InputSummary 强类型对象

        :param args: 函数位置参数元组
        :param kwargs: 函数关键字参数字典
        :return: 填充后的标准化输入摘要模型实例
        """
        ...

    def extract_output(self, result: Any) -> OutputSummary:
        """
        从被装饰函数的执行结果中提取标准化输出摘要

        职责:
            1、解析业务返回值
            2、提取跨系统追踪的关键标识符
            3、评估业务执行的逻辑结果简述

        :param result: 被装饰函数执行后的返回值对象
        :return: 填充后的标准化输出摘要模型实例
        """
        ...

    def supports(self, layer: str, payload_type: Optional[Type[Any]] = None) -> bool:
        """
        策略自发现标识: 判定当前提取器是否能够处理指定的逻辑层级或数据载体类型

        用于 ExtractorFactory 在运行时根据上下文动态选择合适的策略类

        :param layer:
        :param payload_type:
        :return:
        """
        ...
