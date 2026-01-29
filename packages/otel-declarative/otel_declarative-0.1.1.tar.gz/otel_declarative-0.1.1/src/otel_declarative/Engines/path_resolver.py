import os
import jmespath
from jmespath import exceptions
from typing import Any, Dict
from otel_declarative.Enums.extraction_source import ExtractionSource
from otel_declarative.Models.mapping_models import FieldMapping
from otel_declarative.Engines.converter_registry import ConverterRegistry
from otel_declarative.Engines.object_hydrator import ObjectHydrator
from otel_declarative.Logging.logger_factory import get_child_logger

logger = get_child_logger("otel_declarative.Engines", "PathResolver")

class PathResolver:
    """
    路径解析引擎

    职责:
        1、基于 JMESPath 标准在业务上下文中定位原始数据
        2、协调 ConverterRegistry 执行声明式的数据清洗与格式化
        3、提供全链路熔断保护, 确保解析失败时安全回退至默认值
    """

    def __init__(self, converter_registry: ConverterRegistry, object_hydrator: ObjectHydrator):
        """
        :param converter_registry: 注入的转换器注册表实例
        :param object_hydrator: 对象装配引擎
        """
        self._converter_registry = converter_registry
        self._object_hydrator = object_hydrator
        self._env_snapshot = dict(os.environ)
        self._compiled_expressions: Dict[str, Any] = {}

    def resolve(self, context: Dict[str, Any], mapping: FieldMapping) -> Any:
        """
        根据映射规则从执行上下文中解析目标值

        :param context: 包含执行现场数据的字典
        :param mapping: 强类型的字段映射规则模型
        :return: 最终解析并转换后的值
        """
        try:
            # 1、构造统一解析上下文
            search_context: Dict[str, Any] = self._build_search_context(context)
            # 2、调用 JMESPath 执行全量搜索
            current_val: Any = self._apply_jmes_search(search_context, mapping.path)
            if current_val is None:
                return mapping.default

            # 3、执行声明式转换与熔断保护
            if mapping.converter:
                current_val = self._converter_registry.convert(
                    name=mapping.converter,
                    value=current_val,
                    default=mapping.default,
                )
            # 4、执行递归装配逻辑
            if mapping.model_name and current_val is not None:
                return self._object_hydrator.hydrate(
                    raw_data=current_val,
                    mapping=mapping
                )
            return current_val if current_val is not None else mapping.default
        except Exception:
            logger.exception(f"路径解析失败 | 路径: {mapping.path}")
            return mapping.default

    def _build_search_context(self, raw_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        将零散的执行现场组装为统一的观测命名空间

        :param raw_context: 装饰器捕获的原始上下文
        :return: 扁平化的全量检索字典
        """
        # 预先提取位置参数以优化类型嗅探性能
        args_raw: tuple = raw_context.get(ExtractionSource.ARGS.value, ())
        args: list = list(args_raw) if args_raw is not None else []

        return {
            # 位置参数源
            ExtractionSource.ARGS.value: args,
            # 关键字参数源
            ExtractionSource.KWARGS.value: raw_context.get(ExtractionSource.KWARGS.value, {}),
            # 执行结果源
            ExtractionSource.RESULTS.value: raw_context.get(ExtractionSource.RESULTS.value),
            # 环境变量源
            ExtractionSource.ENV.value: self._env_snapshot,
            # 动态类型源
            ExtractionSource.TYPE.value: {
                "args": [type(a).__name__ for a in args] if args else [],
            }
        }

    def _apply_jmes_search(self, root_obj: Any, expression: str) -> Any:
        """
        调用 JMESPath 库执行路径检索

        :param root_obj: 搜索起始对象
        :param expression: JMESPath 表达式
        :return: 检索到的原始数据
        """
        if not expression:
            return root_obj

        try:
            if expression not in self._compiled_expressions:
                self._compiled_expressions[expression] = jmespath.compile(expression)
            compiled_program = self._compiled_expressions[expression]
            return compiled_program.search(root_obj)
        except (exceptions.JMESPathError, Exception):
            logger.exception(f"JMESPath 语法错误 | 表达式: {expression}")
            return None