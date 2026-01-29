from enum import Enum, unique

@unique
class OtelProtocol(str, Enum):
    """
    OpenTelemetry 传输协议枚举
    """
    GRPC = "grpc"
    HTTP = "http"

@unique
class OtelSecurityMode(str, Enum):
    """
    OpenTelemetry 传输安全模式
    """
    # 明文传输, 适合 K8S Pod 间本地通信
    INSECURE = "insecure"
    # 加密传输, 带有证书校验, 适合跨机房或外网
    TLS = "tls"

@unique
class TraceStatus(str, Enum):
    """
    追踪执行状态枚举

    用于标准化 OTel Span 的最终状态标签
    """
    # 业务逻辑正常完成且耗时在 SLA 范围内
    SUCCESS = "success"
    # 捕获到业务逻辑错误或系统级未处理异常
    FAILED = "failed"
    # 业务逻辑虽然成功, 但执行时间超过预设的慢查询阈值
    SLOW = "slow_threshold"

@unique
class TraceStage(str, Enum):
    """
    追踪生命周期阶段枚举

    定义数据路径拦截器在执行过程中的核心拦截点
    """
    # 阶段 1: 拦截器启动阶段, 执行参数捕获
    PRE = "PRE_EXECUTE"
    # 阶段 2: 业务成功返回节点, 执行结果摘要提取
    POST = "POST_EXECUTE"
    # 阶段 3: 异常触发阶段, 执行堆栈跟踪与现场快照记录
    ERROR = "ERROR_EXECUTE"

@unique
class ExtractionSource(str, Enum):
    """
    声明式提取源枚举

    职责:
        1、定义路径解析引擎在执行 JMEPath 检索时的定义命名空间
        2、确保声明式 YAML 配置中的提取路径具有统一的根起点
    """
    # 代指业务函数的位置参数列表
    ARGS = "args"
    # 代指业务函数的关键字参数字典
    KWARGS = "kwargs"
    # 代指业务函数执行完成后的返回值对象
    RESULTS = "results"
    # 代指操作系统环境变量空间
    ENV = "env"
    # 代指被探测对象的运行时 Python 类型信息
    TYPE = "type"

@unique
class ObservabilityInternalNamespace(str, Enum):
    """
    观测引擎内部专用空间枚举

    职责: 统一管理系统内部使用的逻辑标识符, 消除魔术字符串
    """
    # structlog 与 stdlib logging 之间的异步桥接节点名称
    LOG_BRIDGE = "structlog.bridge"
    # 默认观测层级名称
    DEFAULT_LAYER = "otel.declarative"