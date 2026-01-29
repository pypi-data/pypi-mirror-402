import dateparser
import humanize
from glom import glom
from pydantic import TypeAdapter
from typing import Any, Callable, Dict, Union, Set, Optional
from otel_declarative.settings import ObservabilitySettings
from otel_declarative.Enums.converter_types import StandardConverter
from otel_declarative.Logging.logger_factory import get_child_logger

logger = get_child_logger("otel_declarative.Engines", "ConverterRegistry")

class ConverterRegistry:
    """
    基于专业库集成的转换策略注册表

    职责:
        1、利用 dateparser, humanize, glom 等专业库处理复杂数据转换
        2、利用 Pydantic TypeAdapter 实现类型强制转换与熔断
        3、遵循 IoC 原则, 通过配置对象控制转换行为
    """
    def __init__(self, settings: ObservabilitySettings):
        """
        :param settings: 观测性全局配置对象
        """
        self._settings = settings
        self._converters: Dict[str, Callable[[Any], Any]] = {}
        # 异常指纹追踪集, 用于抑制重复的 WARNING 级日志输出
        self._reported_errors: Set[str] = set()
        self._setup_adapters()

    def convert(self, name: str, value: Any, default: Any = None) -> Any:
        """
        执行受保护的声明式转换

        :param name: 转换器名称 (来自 YAML 配置)
        :param value: 原始数据
        :param default: 失败时的回退值
        """
        if value is None:
            return default

        # 执行标准化匹配, 兼容 YAML 中的大小写差异
        lookup_key = self._normalize_key(name)
        adapter: Optional[Callable[[Any], Any]] = self._converters.get(lookup_key)

        if not adapter:
            return value

        try:
            result = adapter(value)
            return result if result is not None else default
        except Exception as e:
            error_fingerprint: str = f"{lookup_key}:{type(e).__name__}"
            if error_fingerprint not in self._reported_errors:
                logger.warning(
                    f"观测引擎断路器 | 转换器: {lookup_key} | "
                    f"错误: {type(e).__name__} | 摘要: {str(e)} | "
                    f"源数据快照: {str(value)[:100]}"
                )
                logger.debug(f"断路器触发堆栈 [{error_fingerprint}]", exc_info=True)
                self._reported_errors.add(error_fingerprint)
            return default

    def _normalize_key(self, key: Union["StandardConverter", str]) -> str:
        """
        统一转换器标识符格式

        将枚举成员或原始字符串转换为统一的查找键

        :param key: 转换器标识符, 支持 StandardConverter 枚举或原始字符串
        :return: 标准化后的字符串键
        """
        raw_key: str = key.value if hasattr(key, "value") else str(key)
        return raw_key.strip().lower()

    def _setup_adapters(self) -> None:
        """
        绑定标准转换器标识符至具体的专业库调用逻辑
        """
        # --- 1、基础类型适配 ---
        self.register(StandardConverter.TO_STR, self._pydantic_adapter(str))
        self.register(StandardConverter.TO_INT, self._pydantic_adapter(int))
        self.register(StandardConverter.TO_BOOL, self._pydantic_adapter(bool))

        # --- 2、时间处理适配 ---
        if self._settings.enable_dateparser:
            self.register(StandardConverter.TO_DATETIME, self._date_adapter)

        # --- 3、格式化适配 ---
        if self._settings.enable_humanize:
            self.register(StandardConverter.HUMAN_SIZE, humanize.naturalsize)
            self.register(StandardConverter.HUMAN_DURATION, humanize.precisedelta)

        # --- 4、结构转换适配 ---
        if self._settings.use_glom_spec:
            self.register(StandardConverter.GLOM_TRANSFORM, self._glom_adapter)

    def register(self, name: Union[StandardConverter, str], func: Callable[[Any], Any]) -> None:
        """
        注册转换器逻辑

        :param name: 转换器标识
        :param func: 具体的转换逻辑函数
        """
        if isinstance(name, StandardConverter):
            lookup_key = self._normalize_key(name)
        elif isinstance(name, str):
            lookup_key = self._normalize_key(name)
        else:
            logger.error(f"无效的转换器名称类型：{type(name)}")
            raise TypeError(f"无效的转换器名称类型：{type(name)}")

        self._converters[lookup_key] = func
        logger.debug(f"转换器注册成功：{lookup_key}")

    # --- 专业库适配器闭包实现 ---

    def _pydantic_adapter(self, target_type: type) -> Callable[[Any], Any]:
        """
        构造基于 Pydantic TypeAdapter 的类型强制转换内核
        """
        adapter = TypeAdapter(target_type)
        return lambda v: adapter.validate_python(v)

    def _date_adapter(self, value: Any) -> Any:
        """
        集成 dateparser 处理模糊时间字符串与时间戳
        """
        if isinstance(value, (int, float)):
            return dateparser.parse(str(value), settings={'TO_TIMEZONE': self._settings.default_timezone})
        return dateparser.parse(value, settings={'TO_TIMEZONE': self._settings.default_timezone})

    def _glom_adapter(self, value: Any) -> Any:
        """
        利用 glom 执行声明式深层结构重塑
        """
        # 注意: 此处 value 预期为元组 (data) 或仅为 data
        if isinstance(value, tuple) and len(value) == 2:
            return glom(value[0], value[1])
        return value