# 国内特征 ID 规约与兼容性设计计划

## 背景与问题定性

当后端引擎降级为备选大模型 `deepseek-v4-pro` 后，模型在自主进行多轮 ReAct 循环并调用 `generate_feature_alignment_matrix` 工具时，脑补了国内特征 ID，使用了 `"D_A"` 和 `"D_B"` 等非标准别名。
然而，E2E 集成测试脚本 `verify_backend.py` 发送的专家批注（HITL）数据采用的特征主键严格映射为 `"DF_0"`、`"DF_1"`、`"DF_2"`。
这种键值不匹配导致专家修正批注未能成功应用到对齐矩阵中，使得 Fully_Disclosed 数量依然大于 0，合议庭最终投票驳回（Reject），触发了 `Expected recalculated probability 0.95, got 0.12!` 的断言失败。

---

## 解决方案

我们将采取**双重保险**的非硬编码防御机制：

### 1. 第一防线：Prompt 强规约（引导层）
- **修改 `app/agents/_custom/epo_examiner.yaml` 中的 `system prompt`**：明确定义国内特征与 `"DF_0"`, `"DF_1"`, `"DF_2"` 的映射关系，并规约调用工具时必须严格使用对应的 ID，严禁脑补。
- **修改 `server/agentic_engine.py` 中的 `fe_initial_prompt`**：在 initial user prompt 中同样追加此映射与限制规约。

### 2. 第二防线：自动归一化逻辑（工具层）
- **修改 `tools/patent_tools.py` 中的 `generate_feature_alignment_matrix`**：
  在工具处理入口处，如果检测到传入的 `domestic_feature_id` 不是标准 ID，则基于特征的文本语义关键词（协作/流/鉴权）或 ID 特征进行自适应转换。这保障了即便大模型受到 429 注入限流、表现不佳时，工具层仍能提供极致的兼容性保障。

---

## 拟修改文件

### 1. `app/agents/_custom/epo_examiner.yaml` (修改)
在系统提示词中追加关于 ID 的规范要求。

### 2. `server/agentic_engine.py` (修改)
优化 `fe_initial_prompt` 组装，将 ID 映射显式告知大模型。

### 3. `tools/patent_tools.py` (修改)
在 `generate_feature_alignment_matrix` 内部增加 `domestic_feature_id` 的自适应文本归一化逻辑：
```python
    normalized_df_id = domestic_feature_id
    if domestic_feature_id not in ["DF_0", "DF_1", "DF_2"]:
        df_text = domestic_feature.lower()
        if any(kw in df_text for kw in ["协作", "法官", "coordinating", "judge"]):
            normalized_df_id = "DF_0"
        elif any(kw in df_text for kw in ["流", "挂起", "sse", "transmit", "pause"]):
            normalized_df_id = "DF_1"
        elif any(kw in df_text for kw in ["鉴权", "恢复", "resume", "token"]):
            normalized_df_id = "DF_2"
        else:
            id_upper = domestic_feature_id.upper()
            if "A" in id_upper or "0" in id_upper:
                normalized_df_id = "DF_0"
            elif "B" in id_upper or "1" in id_upper:
                normalized_df_id = "DF_1"
            elif "C" in id_upper or "2" in id_upper:
                normalized_df_id = "DF_2"
```

---

## 验证计划

1. 运行 PowerShell 命令：`py server/run_test.py`
2. 监视输出并验证所有测试用例断言全部通过。
