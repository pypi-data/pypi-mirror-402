import copy
from pydantic import BaseModel, ValidationError
from typing import Any, Optional, Type, TypeVar, Union, List, Set
from otel_declarative.Engines.model_registry import ModelRegistry
from otel_declarative.Models.mapping_models import FieldMapping
from otel_declarative.Logging.logger_factory import get_child_logger

logger = get_child_logger("otel_declarative.Engines", "ObjectHydrator")

T = TypeVar("T", bound=BaseModel)

class ObjectHydrator:
    """
    对象装配引擎

    职责:
        1、模型检索: 根据规则从 ModelRegistry 获取类定义
        2、结构映射: 将原始字典或列表转化为强类型 Pydantic 对象
        3、熔断保护: 在装配失败时提供防御性降级, 确保不干扰主流程
    """
    def __init__(self, model_registry: ModelRegistry):
        """
        :param model_registry: 模型注册中心实例
        """
        self._model_registry = model_registry
        self._reported_errors: Set[str] = set()

    def hydrate(self, raw_data: Any, mapping: FieldMapping) -> Any:
        """
        执行声明式装配流

        :param raw_data: 由解析内核提取出的原始数据片段
        :param mapping: 包含装配指令的映射规则模型
        :return: 实例化后的对象 / 列表, 或在失败时返回 mapping.default
        """
        # 1、前置校验: 若未声明 model_name, 则不执行装配
        if not mapping.model_name:
            return raw_data

        # 2、检索模型类
        model_class: Optional[Type[BaseModel]] = self._model_registry.get_model(mapping.model_name)
        if not model_class:
            logger.warning(f"装配异常 | 找不到已注册的模型: {mapping.model_name}")
            return self._safe_get_default(mapping.default)

        # 3、分发装配策略
        try:
            if mapping.is_list:
                return self._hydrate_list(data=raw_data, model_class=model_class, default=mapping.default)
            return self._hydrate_single(data=raw_data, model_class=model_class, default=mapping.default)
        except Exception:
            logger.exception(f"装配引擎执行崩溃, 出现未预期错误")
            return self._safe_get_default(mapping.default)

    def _hydrate_single(self, data: Any, model_class: Type[T], default: Any) -> Union[T, Any]:
        """
        执行单对象装配逻辑

        :param data: 原始字典数据
        :param model_class: 目标 Pydantic 类
        :param default: 失败回退值
        :return: 强类型实例
        """
        model_name: str = model_class.__name__

        if not isinstance(data, dict):
            logger.debug(f"装配失败 | 模型 {model_name} 需要字典, 但收到 {type(data).__name__}")
            return self._safe_get_default(default)

        try:
            return model_class.model_validate(data)
        except ValidationError as e:
            fingerprint = f"{model_name}:{len(e.errors())}"
            if fingerprint not in self._reported_errors:
                logger.warning(f"模型校验不通过 | 模型: {model_name}", exc_info=True)
                self._reported_errors.add(fingerprint)
            return self._safe_get_default(default)

    def _hydrate_list(self, data: Any, model_class: Type[T], default: Any) -> Union[List[T], Any]:
        """
        执行对象列表的循环迭代装配, 支持部分元素解析失败的容错机制

        :param data: 原始列表数据
        :param model_class: 目标 Pydantic 类
        :param default: 回退失败值
        :return: 强类型实例列表
        """
        # --- 1、前置类型守卫: 确保输出必须是列表, 否则立即执行断路回退 ---
        if not isinstance(data, list):
            logger.debug(f"装配失败 | 列表模式需要 list, 但收到 {type(data).__name__} | 路径已回退至默认值")
            return self._safe_get_default(default)

        # --- 2、容错迭代装配逻辑 ---
        hydrated_list: List[T] = []
        model_name: str = model_class.__name__
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                logger.warning(f"列表元素装配跳过 | 索引 {index} 处元素预期为 dict, 实际为 {type(item).__name__}")
                continue

            try:
                # 执行 Pydantic 强类型校验与转换
                hydrated_instance: T = model_class.model_validate(item)
                hydrated_list.append(hydrated_instance)
            except ValidationError as e:
                error_count: int = len(e.errors())
                fingerprint: str = f"{model_name}:list_err:{error_count}"
                if fingerprint not in self._reported_errors:
                    logger.warning(f"列表元素装配跳过 | 模型: {model_name} | 索引: {index}", exc_info=True)
                self._reported_errors.add(fingerprint)

        return hydrated_list

    def _safe_get_default(self, default_value: Any) -> Any:
        """
        安全获取默认回退值, 针对可变对象执行深度复制以防止跨 Span 污染

        :param default_value: 映射规则中定义的原始默认值
        :return: 深度复制后的值或原始值
        """
        try:
            if isinstance(default_value, (dict, list)):
                return copy.deepcopy(default_value)
            return default_value
        except Exception:
            return default_value