# 声明式全链路追踪与观测引擎 (OTel-Declarative) 逻辑架构树

## 1. 切面拦截层 (AOP Interception Layer)
*   **ObservabilityProvider** (`provider.py`)
    *   `trace_data_path(layer)`: 核心异步装饰器，定义业务观测切面。
    *   `_handle_pre_execute()`: 拦截函数入口，触发输入元数据提取与 **结构化日志绑定**。
    *   `_handle_post_execute()`: 拦截函数返回，计算 SLA 耗时，同步输出 **Trace** 与 **JSON Log**。
    *   `_handle_error_execute()`: 拦截异常现场，执行堆栈记录与 Span 状态标记。

## 2. 策略工厂与生命周期管理 (IoC & Lifecycle Factory)
*   **ExtractorFactory** (`Factories/extractor_factory.py`)
    *   `_bootstrap_strategies()`: 引导流程，完成组件依赖注入与提取器预热。
    *   `get_extractor(layer)`: 基于逻辑层级分发单例提取器实例。
    *   `reload()`: **[热重载]** 影子容器模式，实现配置与模型的无损原子切换。
*   **ObservabilityEngineState** (`Models/engine_states.py`)
    *   `create_empty()`: Null-Object 模式实现，提供系统引导期的安全占位。
    *   `get_extractor_for_layer()`: 提供线程安全的状态快照读取。
*   **StructuredReporterFactory** (`Reporters/structured_reporter.py`) **[新增]**
    *   `configure_global_logger()`: 编排日志处理器链与异步 Sink 挂载。
    *   `get_logger(layer)`: 获取预绑定业务层级上下文的 structlog 实例。

## 3. 编排与提取层 (Orchestration & Extraction)
*   **GenericExtractor** (`Engines/generic_extractor.py`)
    *   `extract_input(args, kwargs)`: 驱动路径解析引擎执行输入阶段的数据归约。
    *   `extract_output(result)`: 执行结果阶段的数据挖掘。
    *   `supports(layer)`: 判定当前提取器策略与业务层级的匹配性。

## 4. 核心解析内核 (Core Parsing Engines)
*   **PathResolver** (`Engines/path_resolver.py`)
    *   `resolve(context, mapping)`: **[解析大脑]** 协调 JMESPath 检索、数据转换与对象装配。
    *   `_apply_jmes_search()`: 基于预编译表达式的高性能路径检索。
    *   `_build_search_context()`: 构造包含 args, kwargs, results, env 的统一搜索命名空间。
*   **ConverterRegistry** (`Engines/converter_registry.py`)
    *   `convert(name, value)`: 委派专业库（dateparser/humanize/glom）执行声明式数据清洗。
    *   `register(name, func)`: 转换策略动态注册入口。
*   **ObjectHydrator** (`Engines/object_hydrator.py`)
    *   `hydrate(raw_data, mapping)`: 将原始字典/列表递归装配为强类型 Pydantic 对象。
    *   `_hydrate_list()`: 宽容模式的对象列表批量装配逻辑。
    *   `_safe_get_default()`: 防御性深拷贝，防止跨 Trace 的数据污染。
*   **LogProcessorEngine** (`Engines/log_processors.py`) **[新增]**
    *   `OtelTraceContextProcessor`: 动态注入当前活跃 Span 的 `trace_id` 与 `span_id`。
    *   `LogFieldRenamer`: 基于元数据契约执行日志输出 Schema 的动态重映射。
    *   `ServiceMetadataProcessor`: 注入 Pod 名称、服务名等静态环境标识。

## 5. 模型与配置契约 (Data & Configuration Contracts)
*   **ModelRegistry** (`Engines/model_registry.py`)
    *   `discover_models(paths)`: 利用 Python 自省机制自动扫描并发现业务 DTO。
*   **ObservabilityMappingConfig** (`Config/extraction_config.py`)
    *   `load_from_yaml(path)`: 声明式规则加载器，支持 YAML 到强类型 Mapping 的校验转换。
*   **SummaryModels** (`Models/summary_models.py`)
    *   `InputSummary` / `OutputSummary`: 业务元数据载体 DTO。
    *   `to_otel_attributes()`: 将强类型模型扁平化为符合 OTel 规范的 Span 属性集。
*   **LogModels** (`Models/log_models.py`) **[新增]**
    *   `StructureLogSettings`: 定义异步队列深度、JSON 渲染策略等全局参数。
    *   `LogFieldMapping`: 定义日志字段重命名规则的强类型契约。

## 6. 基础支撑层 (Infrastructure Support)
*   **ObservabilitySettings** (`settings.py`)
    *   基于 `BaseSettings` 的环境变量驱动配置，支持 `OBS_` 前缀自动注入。
*   **Constants** (`constants.py`)
    *   `TraceStatus`: 标准化全链路状态枚举 (SUCCESS, FAILED, SLOW)。
    *   `ExtractionSource`: 定义解析引擎的根起点命名空间 (ARGS, KWARGS, RESULTS, ENV, TYPE)。
    *   `ObservabilityInternalNamespace`: 定义内部系统常量（如 Bridge Logger 名称）。
*   **AsyncLogInfrastructure** (`Infrastructure/async_log_engine.py`) **[新增]**
    *   `AsyncLoggingManager`: 封装 `QueueHandler` 与 `QueueListener`，实现 **Log-Produce** 与 **Disk-I/O** 的彻底解耦。
    *   `shutdown()`: 确保容器退出前强制刷新内存日志队列。

---

### 设计原则摘要：
1.  **职责分离**：`PathResolver` 负责“找数据”，`ConverterRegistry` 负责“洗数据”，`ObjectHydrator` 负责“封装数据”，`AsyncLogInfrastructure` 负责“写数据”。
2.  **控制反转**：业务层通过装饰器声明 `layer`，具体的提取算法由 `ExtractorFactory` 在运行时根据 YAML 配置动态注入。
3.  **鲁棒性优先**：全链路采用 `Fail-safe` 设计，任何观测层异常均被拦截并回退至默认值，确保主业务 100% 可靠。
4.  **数据一致性**：Trace 属性与 Log 字段共用同一套提取与上下文注入逻辑，确保**链路-日志**数据的绝对对齐。