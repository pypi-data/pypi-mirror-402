# OTel-Declarative: 声明式全链路追踪与业务观测引擎

`OTel-Declarative` 是一款专为 Python 分布式系统设计的工业级可观测性增强库。它基于 **OpenTelemetry** 标准，通过 **YAML 声明式配置**与 **JMESPath 路径提取**技术，实现了在“零代码侵入”的前提下，动态地从复杂异步函数中捕获核心业务指标并自动注入链路追踪上下文。

同时，它内置了高性能的 **结构化日志 (Structured Logging)** 引擎，支持 `TraceID` 自动注入、异步 I/O 写入与字段动态重映射，打通了“日志”与“链路”之间的数据孤岛。

## 🌟 核心特性

*   **零侵入性**：无需在业务代码中埋点 `span.set_attribute`，仅通过装饰器声明逻辑层级即可。
*   **声明式驱动**：利用 YAML 配置定义数据提取规则，支持 JMESPath 语法精准定位参数、返回值及环境变量。
*   **强类型契约**：集成 Pydantic V2，确保提取出的业务摘要（DTO）具备强类型校验与结构化保证。
*   **日志链路融合**：内置 `structlog` 处理器，自动将 OTel TraceID/SpanID 注入每一行日志，实现“点击链路 -> 查看日志”的无缝跳转。
*   **高性能异步 I/O**：采用 `QueueHandler` + `QueueListener` 架构，将日志写入移至后台线程，确保主业务线程零阻塞（适合 30fps+ 视频流场景）。
*   **工业级鲁棒性**：内置全链路 `Fail-safe` 断路器与错误日志抑制机制，观测层的任何异常均不会干扰主业务流程。
*   **原子化热重载**：支持在不重启服务的情况下，通过影子容器技术原子级更新观测策略与模型。

## 📦 安装

```bash
pip install otel-declarative
```

## 🚀 快速上手

### 1. 定义业务摘要模型 (DTO)
创建一个标准的 Pydantic 模型，用于承载您希望在追踪链路上看到的业务属性。

```python
from pydantic import Field
from otel_declarative.Models import BaseSummary


class StreamInfo(BaseSummary):
    stream_id: str = Field(..., description="流唯一标识")
    bitrate: int = Field(default=0, description="码率")
    codec: str = Field(default="h264")
```

### 2. 编写声明式映射规则 (`observability_mapping.yaml`)
定义如何从函数的 `args`, `kwargs` 或 `results` 中提取数据。

```yaml
layer:
  video_processor:
    input_rules:
      stream_id: 
        path: "args[1].metadata.id"
        default: "unknown_stream"
      payload_type:
        path: "type.args[1]"
    output_rules:
      is_forwarded:
        path: "results.status.is_sent"
        default: false
      stream_info:
        path: "results.data"
        model_name: "StreamInfo"  # 自动触发对象装配逻辑
```

### 3. 集成与装饰
在业务函数上挂载切面，无需修改内部逻辑。系统会自动处理 Span 创建与结构化日志记录。

```python
from otel_declarative import ObservabilityProvider

# 初始化工厂与提供者 (通常在应用启动时)
provider = ObservabilityProvider(settings, extractor_factory, reporter_factory)


@provider.trace_data_path(layer="video_processor")
async def process_video_stream(self, data_packet):
    # 纯净的业务逻辑...
    return {"status": {"is_sent": True}, "data": {"stream_id": "cam_01", "bitrate": 4096}}
```

**运行效果**：
1.  **Jaeger**: 生成名为 `video_processor.process_video_stream` 的 Span，包含 `input.stream_id` 等属性。
2.  **Log**: 自动输出如下结构化日志（自动携带 TraceID）：
    ```json
    {
      "event": "观测切面执行完成",
      "level": "info",
      "timestamp": "2023-10-27T10:00:00Z",
      "trace_id": "a1b2c3d4...", 
      "span_id": "e5f6g7...",
      "service": "deepstream-worker",
      "stage": "POST_EXECUTE",
      "latency": "15.4ms",
      "output.is_forwarded": true
    }
    ```

## ⚙️ 全局配置

系统支持通过环境变量（前缀 `OBS_`）进行全量配置：

| 环境变量 | 描述 | 默认值 |
| :--- | :--- | :--- |
| `OBS_ENABLE_TRACING` | 是否开启全局追踪 | `True` |
| `OBS_SERVICE_NAME` | 注册至 OTel 的服务名称 | `deepstream-worker` |
| `OBS_MAPPING_CONFIG_PATH` | YAML 规则文件路径 | `config/mapping.yaml` |
| `OBS_SLOW_QUERY_THRESHOLD` | 慢查询判定阈值 (秒) | `0.5` |
| `OBS_OTEL__ENDPOINT` | OTLP 采集器端点 | `http://localhost:4317` |
| `OBS_ENABLE_ASYNC_LOG` | 是否开启异步日志写入 | `True` |
| `OBS_LOG_FORMAT` | 日志输出格式 (`json` / `console`) | `json` |

## 🛠️ 高级进阶

### 声明式数据清洗
通过内置的 `ConverterRegistry`，您可以在 YAML 中直接指定数据转换逻辑：

```yaml
# 自动执行类型转换、时间解析或可读化处理
path: "args[1].timestamp"
converter: "to_datetime"  # 集成 dateparser
---
path: "results.file_size"
converter: "human_size"   # 集成 humanize (例如: 1024 -> 1KB)
```

### 结构化日志字段重映射
如果您使用的日志后端（如 ELK, Datadog）对字段名有特殊要求，无需修改代码，只需配置 `LogFieldMapping`：

```python
# 将默认的 'event' 字段重命名为 'message' 以适配 ELK
settings.field_mapping.event = "message"
```

### 业务模型自动发现
引擎启动时会自动扫描 `model_scan_paths` 路径下的所有 Pydantic 模型并注册至 `ModelRegistry`，实现配置名到类定义的动态绑定。

## 🛡️ 鲁棒性保障

*   **路径解析熔断**：若 JMESPath 指向不存在的字段，系统自动回退至 `FieldMapping` 中定义的 `default` 值。
*   **装配降级**：若数据结构不符合 Pydantic 模型定义，系统将仅记录一次降级警告并跳过该属性注入，确保 Trace 不中断。
*   **异步队列保护**：日志写入采用有界队列（默认 1000 条），在极端高压下优先丢弃日志而非阻塞业务，确保主进程稳定性。
*   **内存隔离**：所有提取后的默认值均经过深拷贝（Deepcopy）处理，彻底杜绝跨 Trace 的数据污染。

---

## 🛠️ 开发与测试指南 (Development Guide)

本章节面向项目贡献者与二次开发者，旨在透明化当前的架构局限与未来的优化方向。我们欢迎社区针对以下领域提交 PR。

### 已知缺陷与优化目标 (Roadmap)

#### 1. 核心架构与配置
*   **缺陷**: **单 YAML 文件限制**。
    *   *描述*: 目前 `ExtractorFactory` 仅支持加载单一配置文件，无法处理目录扫描或多文件合并。
    *   *目标*: 实现基于目录通配符 (`config/mappings/*.yaml`) 的配置加载机制，支持模块化管理。
*   **缺陷**: **Output 阶段上下文缺失**。
    *   *描述*: `extract_output` 目前仅能访问 `results`，无法引用入参 `args` 或环境变量 `env`。
    *   *目标*: 扩展上下文构建逻辑，实现 Output 阶段的全生命周期数据访问。
*   **优化**: **Converter 参数化支持**。
    *   *描述*: 当前仅支持无参转换器（如 `to_int`），无法执行如 `truncate(10)` 的操作。
    *   *目标*: 扩展 YAML 解析器以支持带参数的转换指令。

#### 2. 通用性与兼容性
*   **缺陷**: **Payload 位置隐式假设**。
    *   *描述*: `GenericExtractor` 默认假设 `args[1]` 为 payload 对象，这耦合了特定的业务签名。
    *   *目标*: 移除硬编码，改为在 YAML 中提供 `strategy: auto_detect` 或完全由配置驱动。
*   **优化**: **Model 递归扫描**。
    *   *描述*: `discover_models` 目前仅扫描顶层包，不支持子包递归。
    *   *目标*: 引入 `pkgutil.walk_packages` 实现全深度自动发现。

#### 3. 性能与监控
*   **优化**: **JMESPath 编译缓存粒度**。
    *   *描述*: 缓存目前绑定在实例上，热重载后失效。
    *   *目标*: 提升为模块级 LRU Cache，实现跨实例共享。
*   **缺陷**: **缺乏自监控指标 (Self-Observability)**。
    *   *描述*: 引擎内部的性能损耗（如解析耗时、队列积压）对外部不可见。
    *   *目标*: 引入 OTel Metrics，暴露 `otel_declarative_extraction_latency` 等指标。

### 参与贡献
1.  **环境准备**: 使用 Python 3.9+，执行 `pip install -r requirements-dev.txt`。
2.  **单元测试**: 运行 `pytest tests/`，确保覆盖率不低于 85%。
3.  **代码规范**: 遵循 PEP8，使用 `mypy` 进行静态类型检查。

---

## 📄 开源协议
本项目遵循 MIT 协议。