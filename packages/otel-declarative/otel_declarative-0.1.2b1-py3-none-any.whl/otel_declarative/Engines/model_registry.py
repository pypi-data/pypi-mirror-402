import importlib
import inspect
from typing import Dict, Optional, Type, List
from pydantic import BaseModel
from otel_declarative.Logging.logger_factory import get_child_logger

logger = get_child_logger("otel_declarative.Engines", "ModelRegistry")

class ModelRegistry:
    """
    业务观测模型注册中心

    职责:
        1、集中管理所有可用于声明式装配的 Pydantic 模型
        2、实现从模型名称到类定义的动态检索, 支持配置驱动的对象实例化
        3、提供自动发现机制, 减少手动注册的维护成本
    """
    def __init__(self):
        self._models: Dict[str, Type[BaseModel]] = {}
        self._manual_models: List[Type[BaseModel]] = []
        self._is_initialized: bool = False

    def register(self, model_class: Type[BaseModel]) -> None:
        """
        手动注册一个 Pydantic 模型类

        :param model_class: 继承自 pydantic.BaseModel 的类定义
        """
        if not issubclass(model_class, BaseModel):
            logger.warning(f"类 {model_class.__name__} 不是有效的 Pydantic BaseModel, 忽略注册")
            return

        model_name = model_class.__name__
        self._models[model_name] = model_class

        if model_class not in self._manual_models:
            self._manual_models.append(model_class)

        logger.debug(f"已手动注册观测模型: {model_name}")

    def discover_models(self, module_paths: List[str]) -> None:
        """
        扫描指定模块路径下的所有 Pydantic 模型并注册

        :param module_paths: 完整的 Python 模块路径列表 (例如 ['Core.Infrastructure.otel_declarative.Models'])
        """
        for path in module_paths:
            try:
                module = importlib.import_module(path)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseModel) and obj is not BaseModel:
                        self._models[name] = obj
                        logger.info(f"自动发现并注册观测模型: {name} (来自 {path})")
            except ImportError:
                logger.exception(f"无法导入模块执行模型自动发现: {path}")
            except Exception:
                logger.exception(f"模型自动发现过程中发生未预期异常")
        self._is_initialized = True

    def get_model(self, model_name: str) -> Optional[Type[BaseModel]]:
        """
        根据名称检索模型类定义

        :param model_name: 模型类名
        :return: Pydantic 类定义或 None
        """
        return self._models.get(model_name)

    def list_registered_models(self) -> List[str]:
        """
        获取当前所有已注册模型的名称列表
        """
        return list(self._models.keys())

    def get_manual_models(self) -> List[Type[BaseModel]]:
        """
        获取所有手动注册的模型类定义, 用于热重载快照

        :return: 手动注册的模型类列表
        """
        return self._manual_models

    def reset(self) -> None:
        """
        重置注册中心状态
        """
        self._models.clear()
        self._manual_models.clear()
        self._is_initialized = False
        logger.info("模型注册中心已重置")