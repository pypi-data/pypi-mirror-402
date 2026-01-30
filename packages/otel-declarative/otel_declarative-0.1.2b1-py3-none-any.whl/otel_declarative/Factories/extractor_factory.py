from typing import Any, Dict, Optional, List, Type
from otel_declarative.Models.summary_models import BaseModel
from otel_declarative.Models.engine_states import ObservabilityEngineState
from otel_declarative.settings import ObservabilitySettings
from otel_declarative.Config.extraction_config import ObservabilityMappingConfig
from otel_declarative.Interfaces.extractor import IExtractor
from otel_declarative.Engines.generic_extractor import GenericExtractor
from otel_declarative.Engines.path_resolver import PathResolver
from otel_declarative.Engines.converter_registry import ConverterRegistry
from otel_declarative.Engines.model_registry import ModelRegistry
from otel_declarative.Engines.object_hydrator import ObjectHydrator
from otel_declarative.Logging.logger_factory import get_child_logger

logger = get_child_logger("otel_declarative.Factories", "ExtractorFactory")

class ExtractorFactory:
    """
    元数据提取器策略工厂

    职责:
        1、依赖编排: 负责初始化并注入观测基础设施的所有依赖
        2、策略管理: 实现基于逻辑层级的 GenericExtractor 实例生命周期维护
        3、声明式驱动: 启动时加载 YAML 配置并预热所有层级的提取规则
        4、零开销分发: 提供毫秒级的单例策略分发能力
    """
    def __init__(self, settings: ObservabilitySettings):
        """
        :param settings: 观测性全局配置对象
        """
        self._settings: ObservabilitySettings = settings
        self._converter_registry: ConverterRegistry = ConverterRegistry(settings)
        self._state: ObservabilityEngineState = ObservabilityEngineState.create_empty()
        self._bootstrap_strategies()

    def _bootstrap_strategies(self) -> None:
        """
        执行观测系统的启动引导流

        职责:
            1、扫描业务模型并预热注册中心
            2、加载 YAML 映射配置
            3、执行 Fail-safe 策略: 即使引导失败也不抛出异常, 确保主业务可用
        """
        try:
            logger.info(f"正在引导观测性提取引擎策略")

            # 构造影子组件
            model_registry: ModelRegistry = ModelRegistry()
            model_registry.discover_models(self._settings.model_scan_paths)
            mapping_config: ObservabilityMappingConfig = ObservabilityMappingConfig.load_from_yaml(self._settings.mapping_config_path)
            hydrator: ObjectHydrator = ObjectHydrator(model_registry)
            resolver: PathResolver = PathResolver(converter_registry=self._converter_registry, object_hydrator=hydrator)

            # 预热提取器实例映射
            extractors: Dict[str, IExtractor] = {
                layer_name: GenericExtractor(layer=layer_name, rules=rules, resolver=resolver)
                for layer_name, rules in mapping_config.layer.items()
            }

            # 原子切换至就绪状态
            self._state = ObservabilityEngineState(
                model_registry=model_registry,
                object_hydrator=hydrator,
                path_resolver=resolver,
                extractors=extractors,
                is_ready=True
            )
            logger.info(f"观测性策略工厂引导完成，已就绪层级: {list(extractors.keys())}")
        except Exception as e:
            self._state = ObservabilityEngineState.create_empty()
            logger.exception(
                f"观测性策略工厂引导失败 | 错误原因: {str(e)} | 系统将进入 '零观测' 模式运行"
            )

    def get_extractor(self, layer: str, payload: Optional[Any] = None) -> Optional[IExtractor]:
        """
        [核心入口] 根据上下文获取匹配的提取器

        :param layer: 装饰器声明的逻辑层级标识
        :param payload: (可选) 运行时业务载体, 用于未来的动态启发式匹配
        :return: 配置化的提取器实例, 若层级未定义则返回 None
        """
        current_snapshot: ObservabilityEngineState = self._state
        return current_snapshot.get_extractor_for_layer(layer)

    def reload(self) -> None:
        """
        执行观测策略的热重载逻辑

        逻辑:
            1、构造局部影子容器, 隔离重载过程中的中间状态
            2、在影子容器中执行全量引导流 (模型发现 > 配置加载 > 实例预热)
            3、校验成功后执行原子引用替换
            4、若任何环节失败, 丢弃影子容器并保留原始引用, 确保旧策略完整
        """
        logger.info(f"观测性策略工厂正在尝试热重载")

        old_state: ObservabilityEngineState = self._state
        manual_models: List[Type[BaseModel]] = old_state.model_registry.get_manual_models()

        try:
            # --- 1、构造影子内核 ---
            temp_model_registry: ModelRegistry = ModelRegistry()
            temp_model_registry.discover_models(self._settings.model_scan_paths)
            # 恢复手动注册的模型
            for model_cls in manual_models:
                temp_model_registry.register(model_cls)

            # --- 2、加载并校验 YAML 规则 ---
            mapping_config: ObservabilityMappingConfig = ObservabilityMappingConfig.load_from_yaml(
                self._settings.mapping_config_path
            )

            # --- 3、组装影子解析链路 ---
            temp_hydrator: ObjectHydrator = ObjectHydrator(temp_model_registry)
            temp_resolver: PathResolver = PathResolver(converter_registry=self._converter_registry, object_hydrator=temp_hydrator)

            # --- 4、预实例化所有提取器 ---
            temp_extractors: Dict[str, IExtractor] = {
                layer_name: GenericExtractor(layer=layer_name, rules=rules, resolver=temp_resolver)
                for layer_name, rules in mapping_config.layer.items()
            }

            self._state = ObservabilityEngineState(
                model_registry=temp_model_registry,
                object_hydrator=temp_hydrator,
                path_resolver=temp_resolver,
                extractors=temp_extractors,
                is_ready=True
            )
            logger.info(
                f"观测性策略热重载成功，已动态更新层级: {list(temp_extractors.keys())}"
                f"已注册模型数: {len(temp_model_registry.list_registered_models())}"
            )
        except Exception:
            logger.exception(
                f"观测性策略热重载失败 | "
                f"操作建议: 请检查 YAML 语法或 Pydantic 模型定义 | 已执行 Fail-back，保留旧策略运行"
            )

    @property
    def is_healthy(self) -> bool:
        """
        暴露工厂的运行健康状态
        """
        current_snapshot: ObservabilityEngineState = self._state
        return current_snapshot.is_ready and len(current_snapshot.extractors) > 0

    @property
    def model_registry(self) -> ModelRegistry:
        """
        暴露当前活跃的模型注册中心引用

        :return: 当前活跃的 ModelRegistry 实例
        """
        return self._state.model_registry