from enum import Enum, unique

@unique
class ConverterCategory(str, Enum):
    """
    转换器逻辑分类
    """
    # 基础类型
    PRIMITIVE = "primitive"
    # 时间处理
    TEMPORAL = "temporal"
    # 格式化
    FORMAT = "format"
    # 结构重塑
    STRUCTURAL = "structural"
    # 语义校验
    SEMANTIC = "semantic"

@unique
class StandardConverter(str, Enum):
    """
    标准转换器标识符
    """
    # Primitive
    TO_STR = "to_str"
    TO_INT = "to_int"
    TO_BOOL = "to_bool"

    # Temporal
    TO_DATETIME = "to_datetime"
    TO_TIMESTAMP = "to_timestamp"

    # Format
    HUMAN_SIZE = "human_size"
    HUMAN_DURATION = "human_duration"

    # Structural
    GLOM_TRANSFORM = "glom_transform"

    # Semantic
    TO_IP = "to_ip"
    TO_UUID = "to_uuid"