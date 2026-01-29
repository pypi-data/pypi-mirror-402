from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

class FieldMapping(BaseModel):
    """
    单字段提取映射规则模型

    职责:
        1、定义数据提取的路径契约
        2、定义路径失效时的回退机制
        3、声明可选的数据清洗逻辑
    """
    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        extra="ignore"
    )

    # --- 基础路径提取配置 ---
    path: str = Field(
        ...,
        description="基于 JMESPath 标准的数据提取路径, 以 ExtractionSource 为起始点",
        examples=["args.1.stream_id", "env.POD_NAME"]
    )
    default: Any = Field(
        default=None,
        description="路径解析失效时的默认回退值"
    )

    # --- 数据转换配置 ---
    converter: Optional[str] = Field(
        default=None,
        description="关联在 ConverterRegistry 中的转换器标识符 (例如: 'to_int', 'to_upper', 'to_bool')"
    )

    # --- 递归装配配置 ---
    model_name: Optional[str] = Field(
        default=None,
        description="关联在 ModelRegistry 中的自定义 Pydantic 模型类名, 若指定, 解析引擎将执行对象装配逻辑"
    )

    is_list: bool = Field(
        default=False,
        description="声明提取结果是否为对象列表, 若为 True, 引擎将对列表中的每个字典元素执行模型装配"
    )

    @field_validator("path")
    @classmethod
    def validate_path_syntax(cls, v: str) -> str:
        """
        验证器: 确保提取路径不为空且符合基础语法要求

        :param v: 路径字符串
        :return: 验证后的路径
        :raises: ValueError - 当路径格式非法时抛出
        """
        if not v or not v.strip():
            raise ValueError("提取路径 (path) 不能为空")

        # TODO: 此处未来可扩展 JMESPath 语法的静态合规性预检查
        return v.strip()

    def __repr__(self) -> str:
        """
        提供更具可读性的调试输出格式
        """
        hydration_info = f" -> {self.model_name}" if self.model_name else ""
        list_suffix = "[]" if self.is_list else ""
        return f"<FieldMapping path='{self.path}'{hydration_info}{list_suffix} default={self.default}>"

class LayerMappingRules(BaseModel):
    """
    分层提取规则聚合模型

    职责:
        1、聚合特定业务层级在全生命周期内的观测规则
        2、分别定义输入阶段和输出阶段的提取契约
        3、为 ExtractorFactory 提供标准化的配置输入
    """
    model_config = ConfigDict(frozen=True)

    # 输入规则映射: 键名为 InputSummary 模型中的字段名, 值对应提取规则
    input_rules: Dict[str, FieldMapping] = Field(
        default_factory=dict,
        description="InputSummary 的字段映射配置"
    )
    # 输出规则映射: 键名为 OutputSummary 模型中的字段名, 值位对应的提取规则
    output_rules: Dict[str, FieldMapping] = Field(
        default_factory=dict,
        description="OutputSummary 的字段映射配置"
    )

    def __repr__(self) -> str:
        """
        提供更清晰的调试信息
        """
        return f"<LayerMappingRules input_fields={list(self.input_rules.keys())} output_fields={list(self.output_rules.keys())}>"

    @property
    def has_input_rules(self) -> bool:
        """
        判定是否存在输入提取定义
        """
        return len(self.input_rules) > 0

    @property
    def has_output_rules(self) -> bool:
        """
        判定是否存在输出提取定义
        """
        return len(self.output_rules) > 0