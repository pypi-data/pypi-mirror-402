"""
------------------------------ 扩展设计说明 ------------------------------
# 1、为什么不使用全局变量:
#   我们通过 GlobalDependencyContainer 统一管理状态, API 代理层不持有任何具体的引擎实例, 而是通过 BootstrapManager 这一 IoC 入口动态换取
# 2、线程安全保障:
#   BootstrapManager.ensure_initialized 内部使用了 RLock, 确保了在多线程/协程环境下, 并发触发第一个 declarative_trace 时, 系统能且仅能被引导一次
# 3、性能损耗:
#   由于采用了 Lazy Load, 系统在 import 阶段几乎没有任何开销, 首次调用后的后续调用均能通过 container.is_initialized 的快速路径直接返回
------------------------------------------------------------------------
"""

import functools
from typing import Any, Callable, TypeVar, cast
from otel_declarative.Bootstrap.manager import BootstrapManager
from otel_declarative.Bootstrap.container import GlobalDependencyContainer

T = TypeVar("T", bound=Callable[..., Any])

def declarative_trace(layer: str) -> Callable[[T], T]:
    """
    声明式全链路追踪与观测装饰器

    职责:
        1、延迟引导: 再装饰器包装的函数首次执行时, 自动触发引擎的初始化流程
        2、零配置接入: 业务开发方仅需导入该装饰器并知道业务层级, 无需关心底层的配置嗅探与 OTel 注入逻辑
        3、安全降级: 若引导管理器初始化失败, 该代理将自动降级为透传模式
        4、上下文透明: 装饰器内部自动处理异步函数的上下文传递, 确保拦截逻辑对业务逻辑透明

    :param layer: 逻辑层级标识符, 该值必须与 YAML 映射配置文件中的层级名称严格对应
    :return: 一个符合 Python 装饰器协议的可调用对象, 支持异步业务函数
    """
    def decorator(func: T) -> T:
        """
        内部包装器: 接收业务函数并返回增强后的函数
        """
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            异步执行现场: 在每次业务调用时执行状态判定
            """
            # 获取全局依赖容器
            container: GlobalDependencyContainer = BootstrapManager.ensure_initialized()

            # 判定观测引擎是否就绪
            if container.is_initialized and container.provider:
                if container.settings and container.settings.enable_tracing:
                    # 委派执行
                    provider = container.provider
                    # 获取该层级对应的具体拦截逻辑装饰器并对原始函数进行包装
                    interceptor: Callable[[T], T] = provider.trace_data_path(layer)
                    decorated_func = interceptor(func)
                    return await decorated_func(*args, **kwargs)
            return await func(*args, **kwargs)
        # 返回符合原始函数签名的代理包装函数
        return cast(T, wrapper)
    return decorator