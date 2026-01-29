from dataclasses import dataclass
from enum import unique, Enum
from typing import runtime_checkable, Protocol, Any, Dict

# --- 基础契约模块 ---

@dataclass(frozen=True)
class FieldContract:
    """
    定义字段的观测协议元数据
    """
    source_key: str = ""
    is_renamable: bool = False


@unique
class LogFormat(str, Enum):
    """
    结构化日志输出格式枚举

    职责:
        1、定义渲染器的策略标识
        2、区分面向人类阅读的控制台模式与面向机器处理的 JSON 模式
    """
    # 适合开发环境, 带有颜色与缩进
    CONSOLE = "console"
    # 适合生产环境, 标准 JSON 行格式
    JSON = "json"


@runtime_checkable
class ILogProcessor(Protocol):
    """
    结构化日志处理器接口协议

    职责: 定义标准 structlog 中间件必须遵循的函数签名契约
    """
    def __call__(self, logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行日志事件处理逻辑

        :param logger: 当前绑定的 Logger 实例 (BindableLogger、stdlib Logger 等)
        :param method_name: 触发日志的方法名
        :param event_dict: 当前上下文累积的日志数据字典
        :return: 处理或增强后的新事件字典
        """
        ...
