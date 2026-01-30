from typing import Any, Dict, Optional, Type
from otel_declarative.Interfaces.extractor import IExtractor
from otel_declarative.Models.mapping_models import LayerMappingRules
from otel_declarative.Models.summary_models import InputSummary, OutputSummary
from otel_declarative.Engines.path_resolver import PathResolver
from otel_declarative.Enums.extraction_source import ExtractionSource
from otel_declarative.Logging.logger_factory import get_child_logger

logger = get_child_logger("otel_declarative.Engines", "GenericExtractor")

class GenericExtractor(IExtractor):
    """
    通用声明式提取器

    职责:
        1、流程编排: 按照声明式规则 (LayerMappingRules) 驱动路径解析引擎执行数据挖掘
        2、数据归约: 将解析后的异构数据片段组装并校验为强类型的 DTO 模型
        3、策略解耦: 自身不包含任何业务代码, 所有的提取逻辑由注入的映射规则决定
    """
    def __init__(self, layer: str, rules: LayerMappingRules, resolver: PathResolver):
        """
        :param layer: 当前提取器所属的逻辑层级标识符
        :param rules: 存储在内存中的强类型提取规则映射表
        :param resolver: 注入的路径解析引擎实例
        """
        self._layer: str = layer
        self._rules: LayerMappingRules = rules
        self._resolver: PathResolver = resolver

    def extract_input(self, args: Any, kwargs: Any) -> InputSummary:
        """
        执行函数入口阶段的数据提取与模型装配

        逻辑:
            1、组装基础解析上下文
            2、遍历 input_rules 委派 resolver 提取数据
            3、执行属性自动补全与鲁棒性校验
            4、生成强类型 InputSummary 实例

        :param args: 业务函数的位置参数元组
        :param kwargs: 业务函数的关键字参数字典
        :return: 经过 Pydantic 校验的标准化输入摘要模型
        """
        # 1、构造统一的解析上下文命名空间
        extraction_context: Dict[str, Any] = {
            ExtractionSource.ARGS.value: args,
            ExtractionSource.KWARGS.value: kwargs
        }
        # 2、遍历声明式规则执行数据收集
        extracted_fields: Dict[str, Any] = {}
        for field_name, mapping_rule in self._rules.input_rules.items():
            # 委派解析引擎执行深度路径搜索与数据清洗
            extracted_fields[field_name] = self._resolver.resolve(context=extraction_context, mapping=mapping_rule)

        # 3、自动嗅探缺失的元数据
        current_payload_type = extracted_fields.get("payload_type")
        if not current_payload_type or current_payload_type == "Unknown":
            if len(args) > 1:
                # 按照约定, args[1] 通常为业务负载对象
                extracted_fields["payload_type"] = type(args[1]).__name__
            else:
                extracted_fields["payload_type"] = "Unknown"

        # 4、兜底
        if not extracted_fields.get("pod_name"):
            extracted_fields["pod_name"] = "unspecified-pod"

        return InputSummary.model_validate(extracted_fields)

    def extract_output(self, result: Any) -> OutputSummary:
        """
        执行函数返回阶段的数据提取与模型装配

        :param result: 业务逻辑处理完成后的返回值对象
        :return: 经过 Pydantic 校验的标准化输出摘要模型
        """
        # 1、构造结果阶段解析上下文
        extraction_context: Dict[str, Any] = {
            ExtractionSource.RESULTS.value: result
        }
        # 2、遍历输出映射规则, 执行数据收集
        extracted_fields: Dict[str, Any] = {}
        for field_name, mapping_rule in self._rules.output_rules.items():
            extracted_fields[field_name] = self._resolver.resolve(context=extraction_context, mapping=mapping_rule)
        # 3、执行最终模型校验
        return OutputSummary.model_validate(extracted_fields)

    def supports(self, layer: str, payload_type: Optional[Type[Any]] = None) -> bool:
        """
        判定当前实例是否能够支持指定的观测层级

        :param layer: 装饰器传入的逻辑层级标识
        :param payload_type: 运行时的 Payload 类型, 供动态嗅探使用
        :return: 布尔值, 标识是否匹配
        """
        return self._layer == layer