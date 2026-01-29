import time
import functools
import structlog
from datetime import datetime, timezone
from typing import Any, Callable, Optional, TypeVar, cast, Dict
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, Span, Tracer
from otel_declarative.settings import ObservabilitySettings
from otel_declarative.constants import TraceStatus, TraceStage
from otel_declarative.Models.summary_models import InputSummary, OutputSummary
from otel_declarative.Factories.extractor_factory import ExtractorFactory
from otel_declarative.Interfaces.extractor import IExtractor
from otel_declarative.Reporters.structured_reporter import StructuredReporterFactory

T = TypeVar("T", bound=Callable[..., Any])

class ObservabilityProvider:
    """
    观测性组件提供者

    职责:
        1、链路编排: 管理 OpenTelemetry Span 的生命周期
        2、策略映射: 调用 ExtractorFactory 为不同业务层级匹配声明式提取器
        3、属性注入: 将提取出的强类型摘要数据转换为 Span Attributes
        4、性能剖析: 自动度量业务函数的执行耗时并执行 SLA 判定
    """
    def __init__(self, settings: ObservabilitySettings, extractor_factory: ExtractorFactory, reporter_factory: StructuredReporterFactory):
        """
        :param settings: 观测性全局配置对象
        :param extractor_factory: 预初始化完成的策略提取器工厂
        :param reporter_factory: 具备异步桥接能力的结构化记录器工厂
        """
        self._settings: ObservabilitySettings = settings
        self._extractor_factory: ExtractorFactory = extractor_factory
        self._reporter_factory: StructuredReporterFactory = reporter_factory
        # 获取标准 OTel Tracker 单例
        self._tracer: Tracer = trace.get_tracer(self._settings.service_name)
        # 初始化基础设施层记录器
        self._infra_logger = self._reporter_factory.get_logger("otel_declarative.Infrastructure")

    def trace_data_path(self, layer: str) -> Callable[[T], T]:
        """
        构造数据路径追踪切片的异步装饰器

        逻辑:
            1、透明拦截异步函数调用现场
            2、自动获取对应层级的结构化 BoundLogger
            3、管理全生命周期中的 PRE >> EXECUTE >> POST / ERROR 观测流
            4、自动清理上下文环境

        :param layer: 逻辑分层标识符 (需在 YAML 配置中定义对应的映射规则)
        :return: 异步函数装饰器
        """
        def decorator(func: T) -> T:
            @functools.wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                if not self._settings.enable_tracing:
                    return await func(*args, **kwargs)

                # 每次调用前先清理上下文, 防止线程复用污染
                structlog.contextvars.clear_contextvars()
                log = self._reporter_factory.get_logger(layer)

                # 启动 OTel Span
                # 注: Span 名称约定使用 'Layer.FunctionName' 格式, 以优化 Jaeger 展示
                span_name = f"{layer}.{func.__qualname__}"
                with self._tracer.start_as_current_span(span_name) as span:
                    # 执行 PRE 阶段
                    extractor: Optional[IExtractor] = self._handle_pre_execute(
                        span=span,
                        layer=layer,
                        args=args,
                        kwargs=kwargs,
                        log=log
                    )

                    start_pref = time.perf_counter()
                    try:
                        # 执行业务主逻辑
                        result = await func(*args, **kwargs)

                        # 执行 POST 阶段
                        execution_duration = time.perf_counter() - start_pref
                        self._handle_post_execute(
                            span=span,
                            layer=layer,
                            extractor=extractor,
                            result=result,
                            duration_sec=execution_duration,
                            log=log
                        )

                        return result
                    except Exception as e:
                        self._handle_error_execute(
                            span=span,
                            layer=layer,
                            exception=e,
                            log=log
                        )
                        raise e
                    finally:
                        structlog.contextvars.clear_contextvars()

            return cast(T, wrapper)
        return decorator

    def _handle_pre_execute(self, span: Span, layer: str, args: Any, kwargs: Any, log: Any) -> Optional[IExtractor]:
        """
        处理进入业务函数前的观测逻辑

        :param span: 当前活跃的 Span 实例
        :param layer: 逻辑层级标识
        :param args: 原始位置参数
        :param kwargs: 原始关键字参数
        :param log: 绑定的结构化记录器实例
        :return: 匹配到的通用提取器实例 (供 POST 阶段复用)
        """
        try:
            # 从工厂获取声明式提取器
            extractor: Optional[IExtractor] = self._extractor_factory.get_extractor(layer)
            if not extractor:
                return None

            # 执行基于 YAML 规则的数据提取
            input_dto: InputSummary = extractor.extract_input(args, kwargs)

            # 注入 OTel 属性
            attributes: Dict[str, Any] = input_dto.to_otel_attributes()
            for k, v in attributes.items():
                span.set_attribute(k, v)
            # 将提取的业务上下文绑定至 structlog
            structlog.contextvars.bind_contextvars(**attributes)
            log.info(f"观测切面入口触发", stage=TraceStage.PRE.value, **attributes)

            # 记录生命周期事件
            span.add_event(TraceStage.PRE.value, {"at": datetime.now(timezone.utc).isoformat()})
            return extractor
        except Exception:
            self._infra_logger.exception(f"观测路径提取失败 [PRE]", layer=layer, stage=TraceStage.PRE.value)
            return None

    def _handle_post_execute(self, span: Span, layer: str, extractor: Optional[IExtractor], result: Any, duration_sec: float, log: Any) -> None:
        """
        处理业务成功返回后的观测逻辑

        :param span: 当前活跃的 Span 实例
        :param layer: 逻辑层级标识
        :param extractor: 之前匹配到的提取器
        :param result: 业务执行结果
        :param duration_sec: 业务逻辑真实执行时长
        :param log: 绑定的结构化记录器实例
        """
        try:
            # 1、提取输出摘要
            output_attributes: Dict[str, Any] = {}
            if extractor:
                output_dto: OutputSummary = extractor.extract_output(result)
                output_attributes = output_dto.to_otel_attributes()
                # 修正: 循环调用单数形式的 set_attribute 以符合 API 签名
                for k, v in output_dto.to_otel_attributes().items():
                    span.set_attribute(k, v)

            # 2、性能画像与 SLA 判定
            duration_ms = duration_sec * 1000
            span.set_attribute("performance.duration_ms", duration_ms)

            trace_status_value: str
            if duration_sec > self._settings.slow_query_threshold:
                trace_status_value = TraceStatus.SLOW.value
                span.set_attribute("trace.status", TraceStatus.SLOW.value)
                span.set_status(Status(StatusCode.OK, f"SLA Violation: {duration_ms:.2f}ms"))
            else:
                trace_status_value = TraceStatus.SUCCESS.value
                span.set_attribute("trace.status", TraceStatus.SUCCESS.value)
                span.set_status(Status(StatusCode.OK))

            log.info(
                f"观测切面执行完成",
                stage=TraceStage.POST.value,
                latency=f"{duration_ms:.2f}ms",
                trace_status=trace_status_value,
                **output_attributes,
            )


            span.add_event(TraceStage.POST.value, {"latency": f"{duration_ms:.2f}ms"})
        except Exception:
            self._infra_logger.exception(f"观测路径提取失败 [POST]", layer=layer, stage=TraceStage.POST.value)

    def _handle_error_execute(self, span: Span, layer: str, exception: Exception, log: Any) -> None:
        """
        处理业务逻辑崩溃时的异常观测逻辑

        :param span: 当前活跃的 Span 实例
        :param layer: 业务逻辑层级标识
        :param exception: 捕获到的异常对象
        :param log: 绑定的结构化记录器实例
        """
        # 设置 Span 状态为错误, 触发下游报警
        span.set_status(Status(StatusCode.ERROR, str(exception)))
        span.set_attribute("trace.status", TraceStatus.FAILED.value)
        # 自动记录异常堆栈
        span.record_exception(exception)

        # 记录生命周期事件并附加异常信息
        log.error(
            f"观测切面业务崩溃",
            stage=TraceStage.ERROR.value,
            exception=type(exception).__name__,
            exception_message=str(exception),
            exc_info=True
        )
        span.add_event(TraceStage.ERROR.value, {
            "exception.type": type(exception).__name__,
            "exception.message": str(exception)
        })