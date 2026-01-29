from typing import Annotated, Dict, Any, Set
from pydantic import BaseModel, ConfigDict, Field, model_validator
from otel_declarative.Models.Log.constants import FieldContract

# --- 映射规则模块 ---

class LogFieldMapping(BaseModel):
    """
    日志标准字段重映射模型

    职责:
        1、契约定义: 利用 Annotated 语法将业务配置与底层 FieldContract 观测契约进行原子化绑定
        2、静态校验: 强制执行输出键名的唯一性检查, 防止日志数据覆盖
        3、引擎导航: 为 LogFieldRenamer 提供高性能的迁移矩阵预计算基础
    """
    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
    )

    # --- 基础字段 ---
    event: Annotated[
        str,
        Field(default="event", description="业务事件消息的输出键名"),
        FieldContract(source_key="event", is_renamable=True),
    ]

    timestamp: Annotated[
        str,
        Field(default="@timestamp", description="日志产生时间的输出键名"),
        FieldContract(source_key="timestamp", is_renamable=True),
    ]

    level: Annotated[
        str,
        Field(default="level", description="日志级别的输出键名"),
        FieldContract(source_key="level", is_renamable=True),
    ]

    logger: Annotated[
        str,
        Field(default="logger", description="日志记录器名称的输出键名"),
        FieldContract(source_key="logger", is_renamable=True)
    ]

    # --- OTel 追踪字段 ---
    trace_id: Annotated[
        str,
        Field(default="trace_id", description="注入的 OTel TraceID 输出键名"),
        FieldContract(is_renamable=False)
    ]

    span_id: Annotated[
        str,
        Field(default="span_id", description="注入的 OTel SpanID 输出键名"),
        FieldContract(is_renamable=False)
    ]

    # --- 服务元数据字段 ---
    service: Annotated[str,
    Field(default="service", description="服务唯一名称的输出键名"),
    FieldContract(is_renamable=False)
    ]

    environment: Annotated[str,
    Field(default="environment", description="运行环境标识的输出键名"),
    FieldContract(is_renamable=False)
    ]

    pod_name: Annotated[str,
    Field(default="pod_name", description="K8S Pod/节点名称的输出键名"),
    FieldContract(is_renamable=False)
    ]

    @model_validator(mode="after")
    def validate_no_target_key_collision(self) -> "LogFieldMapping":
        """
        后验校验: 确保所有的目标键名在日志 Schema 中具有唯一性

        职责: 防止用户在 YAML 配置中错误的将两个不同的字段映射到同一个 Key, 导致日志数据覆盖

        :return: 校验后的实例
        :raises: ValueError - 当检测到键名冲突时抛出
        """
        target_keys: Dict[str, Any] = self.model_dump()
        seen_keys: Set[str] = set()
        for attr_name, target_key in target_keys.items():
            if target_key in seen_keys:
                raise ValueError(
                    f"日志字段映射冲突: 多个配置项指向了同一个目标键名 '{target_key}'"
                    f"请检查模型属性 '{attr_name}' 的配置"
                )
            seen_keys.add(target_key)
        return self
