from enum import Enum, unique

@unique
class ExtractionSource(str, Enum):
    """
    提取来源枚举

    定义路径解析引擎 (PathResolver) 可访问的顶级命名空间
    """
    # 函数位置参数列表 (元组)
    ARGS = "args"
    # 函数关键字参数字典
    KWARGS = "kwargs"
    # 业务函数执行后的返回值
    RESULTS = "results"
    # 系统环境变量 (os.environ)
    ENV = "env"
    # 对象的 Python 类型信息 (用于类型嗅探)
    TYPE = "type"