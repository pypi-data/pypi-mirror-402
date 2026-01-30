import decimal
import ipaddress
import pendulum
import humanize
import dateparser
from glom import glom
from dateparser.conf import Settings
from typing import Any, Annotated, Final, cast
from pydantic import TypeAdapter, BeforeValidator

class ConverterStrategies:
    """
    转换策略静态工具集

    职责:
        1、封装无状态、纯函数式的标准转换逻辑
        2、集成 Decimal、Pendulum、IpAddress 等专业库处理边缘情况
        3、提供宽容与精确性并存的数据清洗能力
    """

    # --- 内部验证钩子 ---

    @staticmethod
    def _tolerant_int_pre_validator(v: Any) -> Any:
        """
        宽容整数预处理器

        策略:
            利用 Decimal 执行高精度截断操作, 避免 float 二进制近似带来的转换误差

        :param v: 任意输入值
        :return: 预处理后的整数或原始值
        """
        try:
            if isinstance(v, (float, str)):
                return int(decimal.Decimal(str(v)).to_integral_value(rounding=decimal.ROUND_DOWN))
        except (ValueError, TypeError, decimal.InvalidOperation):
            pass
        return v

    TolerantInt: Final = Annotated[int, BeforeValidator(_tolerant_int_pre_validator)]

    # --- 公开策略方法 ---

    @staticmethod
    def to_string(value: Any) -> str:
        """
        策略: 强制转换为字符串
        """
        return TypeAdapter(str).validate_python(value)

    @staticmethod
    def to_int(value: Any) -> str:
        """
        策略: 强制转换为整数 (Decimal 高精度截断)

        :raises: ValidationError
        """
        return TypeAdapter(ConverterStrategies.TolerantInt).validate_python(value)

    @staticmethod
    def to_bool(value: Any) -> bool:
        """
        策略: 强制转换为布尔值
        """
        return TypeAdapter(bool).validate_python(value)

    @staticmethod
    def to_datetime(value: Any, timezone: str = "UTC") -> Any:
        """
        策略: 转换为 datetime 对象 (混合引擎)

        逻辑：
            1、优先使用 Pendulum 库尝试精确解析 (RFC 3339 / ISO 8601)
            2、若失败, 降级至 Dateparser 执行模糊自然语言推断

        :param timezone: 模板时区名称
        """
        try:
            dt = pendulum.parse(str(value), tz=timezone)
            if isinstance(dt, pendulum.DateTime):
                return dt
        except Exception:
            pass

        # 降级至 Dateparse 模糊解析
        settings_obj = Settings({"TO_TIMEZONE": timezone})
        if isinstance(value, (int, float)):
            return dateparser.parse(str(value), settings=cast(Any, settings_obj))
        return dateparser.parse(value, settings=cast(Any, settings_obj))

    @staticmethod
    def to_ipv4(value: Any) -> str:
        """
        策略: 转换为标准 IPv4 字符串

        :param value: IP 字符串或整数
        :return: 标准点分十进制字符串
        :raises: ValueError - 当 IP 格式非法时抛出
        """
        try:
            return str(ipaddress.IPv4Address(value))
        except ipaddress.AddressValueError as e:
            raise ValueError(f"无效的 IPv4 地址：{value}") from e

    @staticmethod
    def human_size(value: Any) -> str:
        """
        策略: 转换为人性化字节大小
        """
        return humanize.naturalsize(value)

    @staticmethod
    def glom_transform(value: Any) -> Any:
        """
        策略: 执行 glom 结构变换
        """
        if isinstance(value, tuple) and len(value) == 2:
            return glom(value[0], value[1])
        return value