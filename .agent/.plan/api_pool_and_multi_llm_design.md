# PatentX 声明式 API 池与多 LLM 混合接入技术方案

基于与用户的 `/grill-me` 深度对齐，确立了声明式 API 池适配器与多 LLM 绑定的核心架构方案。

## 1. 声明式 API 池架构 (Declarative API Pool)

为了将外部专利数据库（EPO OPS, Google Patents BigQuery, The Lens API）与 Agent 本身完全解耦，引入全局统一配置的 API 池适配器设计。

### 1.1 全局配置示例 (`api_pool.yaml`)
```yaml
# api_pool.yaml
# 全局数据源适配器配置

adapters:
  epo_ops:
    class_path: "server.adapters.epo_ops_adapter.EpoOpsAdapter"
    auth:
      consumer_key: "${ENV_EPO_CONSUMER_KEY}"
      consumer_secret: "${ENV_EPO_CONSUMER_SECRET}"
    rate_limit: "10/min"
    mock_fallback: true

  google_bigquery:
    class_path: "server.adapters.bigquery_adapter.BigQueryAdapter"
    project_id: "patentx-gcp-project"
    credentials_json: "${ENV_GCP_CREDENTIALS}"
    mock_fallback: true

  the_lens:
    class_path: "server.adapters.lens_adapter.LensAdapter"
    token: "${ENV_LENS_TOKEN}"
    mock_fallback: true
```

### 1.2 依赖注入与工具生成
1.  **适配器实例化**：系统启动时，L0 编排器加载 `api_pool.yaml`，根据 `class_path` 动态实例化各 API 适配器（Adapters）。
2.  **前置钩子（PII 脱敏）**：适配器在发起外部请求前，拦截请求参数，调用 `pii_filter` 组件脱敏敏感信息。
3.  **后置钩子（数据精炼）**：适配器拿到外部 API 的原始数据（如 XML/JSON 报文）后，自动进行格式清洗与摘要精炼，转换为 RAG 所需的标准 `CleanText` 与特征对齐矩阵结构，再写入全局黑板。
4.  **注入 Agent**：在 Agent YAML 配置文件中声明其依赖的工具。系统运行时将初始化好的适配器实例方法作为 Tool 挂载注入给对应的 Agent。

---

## 2. 多 LLM 混合编排架构 (Multi-LLM Hybrid Orchestration)

支持每个层级的 Agent 根据工作特性配置和调用不同的 LLM 模型底座。

### 2.1 声明式配置绑定
在各 Agent 配置文件中直接声明 `llm` 属性：

*   **L1 法官 Agent (`patent_judge.yaml`)**：
    ```yaml
    name: patent_judge
    layer: 1
    llm:
      provider: "google"
      model: "gemini-1.5-pro"
      temperature: 0.2
    ```
*   **L2 专精审查员 Agent (`epo_examiner.yaml`)**：
    ```yaml
    name: epo_examiner
    layer: 2
    llm:
      provider: "google"
      model: "gemini-1.5-flash"
      temperature: 0.1
    ```

### 2.2 LLMFactory 动态装载器
后端运行时核心实现 `LLMFactory` 类：
*   **抽象封装**：统一封装 Google AI SDK、OpenAI SDK 等底座，提供标准的方法 `generate(prompt: str, system_instruction: str) -> str`。
*   **按需实例化**：当系统装载 Agent 时，根据 Agent YAML 里的 `llm` 配置，由 `LLMFactory` 动态生成具体的大模型 Client 实例并注入给 Agent。

---

## 3. 待办开发任务 (Task Breakdown)
*   [ ] 编写 `server/adapters/base_adapter.py` 基类，定义 `retrieve` 与 `clean` 的标准抽象接口。
*   [ ] 编写 `server/adapters/bigquery_adapter.py` 及其他适配器具体类（内置 Mock 降级）。
*   [ ] 创建 `server/llm_factory.py`，支持基于配置的多供应商（Google, OpenAI）模型加载。
*   [ ] 重构 L1/L2 Agent YAML 配置文件，注入各自的 `llm` 参数。
*   [ ] 编写测试脚本，测试多 LLM 加载与 API 适配器注入流。
