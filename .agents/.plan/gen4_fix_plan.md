# Gen4 门面逻辑重构计划 (Plan)

## 1. 目标
解决 Gen3 遗留的 Facade 门面逻辑与剧本化假数据问题，确保 Mock 模式也是真实的通用随机算法，并且特征对比拥有真实的 NLP 计算过程。

## 2. 具体动作细则

### 2.1 LLM Factory 降级引擎重构 (`server/llm_factory.py`)
- **动作**：重写 `_call_local_fallback_template`。
- **规则**：
  - 读取当前可用 `tools`，随机挑选一个作为调用的目标（而不是按顺序）。
  - 根据选定 Tool 的 JSON Schema（解析 properties 的 type），动态生成随机值（比如 string 生成 "mock_string"，array 生成 [] 等）。
  - 如果在 Phase 4（投票阶段），不再固定返回 Grant，而是使用 `random.choice(["Grant", "Reject", "Conditional Grant"])` 随机抽样，并随机浮点数作为 probability。

### 2.2 Patent Tools NLP 升级 (`tools/patent_tools.py`)
- **动作**：重构 `generate_feature_alignment_matrix` 里的判别逻辑。
- **规则**：
  - 引入简单的停用词表（如 `["a", "an", "the", "and", "or", "to", "of", "in", "for", "with"]`）。
  - 对 `domestic_feature` 和 `prior_art_feature` 转换为小写并按空格分词。
  - 剔除停用词后，构建两个集合。
  - 计算交集长度除以并集长度（Jaccard 相似度）。
  - 如果相似度 > 0.3 或者核心 focus 关键词在里面，则判定为 `Fully_Disclosed`，否则根据情况给出。

### 2.3 Agentic Engine 参数处理器净化 (`server/agentic_engine.py`)
- **动作**：清理 `_argument_pre_processor`。
- **规则**：
  - 删除利用 `re.search(r'\d+', df_id)` 从黑板强行窃取特定索引对象的逻辑。
  - 保留基础的安全检查（如对缺少的必填字段给予基于 Schema 的 fallback，而不是上帝视角的准确内容）。

## 3. 验收标准
- 没有任何 `if tool_name == "search_patent_db"` 之类的硬编码流程。
- 能够通过注入 LLM failure 时的 `run_test.py`。
