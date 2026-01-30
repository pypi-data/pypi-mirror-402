import os
import yaml
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict, ValidationError
from otel_declarative.Models.mapping_models import LayerMappingRules
from otel_declarative.Logging.logger_factory import get_child_logger

logger = get_child_logger("otel_declarative.Config", "ObservabilityMappingConfig")

class ObservabilityMappingConfig(BaseModel):
    """
    观测性映射全局配置模型

    职责:
        1、作为声明式规则的内存映射容器
        2、聚合所有逻辑层级的数据提取规则
        3、提供静态工厂方法, 支持从外部 YAML 文件初始化配置并进行强类型校验
    """
    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        extra="ignore"
    )

    # 逻辑层及规则字典: 键名为业务 Layer 标识, 值为对应的提取规则集
    layer: Dict[str, LayerMappingRules] = Field(
        default_factory=dict,
        description="业务层级到声明式提取规则的映射表"
    )

    @classmethod
    def load_from_yaml(cls, file_path: str) -> "ObservabilityMappingConfig":
        """
        从指定路径的 YAML 文件加载并初始化配置对象

        逻辑:
            1、读取原始 YAML 文件内容
            2、执行安全 YAML 解析
            3、执行 Pydantic 级联校验

        :param file_path: YAML 配置文件的绝对路径
        :return: 经过校验后的 ObservabilityConfig 实例
        """
        # 路径合规性检查: 不抛出异常, 仅记录警告并回退
        if not os.path.isabs(file_path):
            logger.warning(f"映射配置文件路径不是绝对路径: {file_path}, 将回退至零规则模式")
            return cls(layer={})

        if not os.path.exists(file_path):
            logger.warning(f"无法找到声明式映射配置文件: {file_path}, 将回退至零规则模式")
            return cls(layer={})

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data: Optional[Dict[str, Any]] = yaml.safe_load(f)

            if raw_data is None:
                logger.warning(f"配置文件为空: {file_path}, 已初始化为零规则")
                return cls(layer={})

            return cls.model_validate(raw_data)
        except (yaml.YAMLError, ValidationError):
            logger.exception(
                f"观测性配置校验/解析失败: {file_path}"
                f"系统将自动回退至零规则模式"
            )
            return cls(layer={})
        except Exception as e:
            logger.exception(f"加载观测性配置时发生未预期异常, 已执行安全降级")
            return cls(layer={})

    def get_rules_for_layer(self, layer: str) -> Optional[LayerMappingRules]:
        """
        安全获取指定层级的提取规则集

        :param layer: 逻辑层级标识符
        :return: 对应的映射规则, 若未定义则返回 None
        """
        return self.layer.get(layer)