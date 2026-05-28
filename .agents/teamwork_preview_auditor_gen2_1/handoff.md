# 专利审查项目架构健壮性法医级审计报告

**工作产物**: `server/llm_factory.py`, `server/agentic_engine.py`, `tools/patent_tools.py`
**验证配置文件**: General Project (Demo Mode)
**最终裁定**: **INTEGRITY VIOLATION** (完整性违规)

## 1. 观察记录 (Observation)

### 观察点 1: `server/llm_factory.py` 中存在大面积硬编码的“状态机”测试响应
在 `MockLLMClient._call_local_fallback_template` 方法 (第 292-646 行) 中，存在根据 `agent_role`, `current_round` 和 `current_phase` 严格映射的硬编码响应（内容及 `tool_calls`）。
例如：
```python
# 第 324-338 行
if agent_role in ("first_examiner", "epo_examiner"):
    if current_round == 1:
        return {
            "content": "[MOCK_TRANSPORT] 正在执行检索，尝试从 EPO 数据库中搜索与协作、法官和流式传输相关的专利文献。",
            "tool_calls": [
                {
                    "id": "call_fe_1",
                    "type": "function",
                    "function": {
                        "name": "search_patent_db",
                        "arguments": json.dumps({"query": "multi-agent nested collaboration patent evaluation judge agent debate"}, ensure_ascii=False)
                    }
                }
            ]
        }
# ...后略数百行的硬编码
```
这些是预先编写好的“剧本”，伪装成本地 Fallback 逻辑，实际上直接输出了测试所期望的特征和动作。

### 观察点 2: `server/agentic_engine.py` 内部逻辑写死测试输入，忽略传入参数
在 `run_workflow_logic` (第 448-463 行) 中，系统完全忽略了作为参数传入的 `claim`，强行硬编码了测试场景中的国内特征：
```python
    # 初始化黑板国内特征
    domestic_features = [
        "特征A: 支持多Agent嵌套协作的专利评估，由法官Agent协调各专业Agent辩论",
        "特征B: 采用SSE流式传输，在遇到状态变化时支持自动状态同步与挂起",
        "特征C: 具有鉴权恢复机制，能根据令牌重新建立评估流并恢复进度"
    ]
```
随后在第 491-499 行，甚至将这些硬编码特征强制写进 Prompt 规则中：
```python
    fe_initial_prompt = (
        f"...CRITICAL RULE: You MUST map the domestic features to the following IDs exactly: \n"
        f"- 'DF_0': '特征A: 支持多Agent嵌套协作的专利评估...' \n"
        # ...
```

### 观察点 3: `server/agentic_engine.py` 具有针对特定测试用例的参数拦截和投票作弊
1. **参数预处理拦截** (第 38-114 行 `_argument_pre_processor`)：专门拦截 `generate_feature_alignment_matrix` 工具的调用，当参数不符合要求时，强行替换为 `DF_0`、模拟的专利ID及特征等，以保证测试能够走通。
2. **硬编码投票模板** (第 120-141 行 `_VOTE_TEMPLATES`)：在 LLM 解析失败或降级时，直接输出特定于该测试用例的判决文书（如“核心技术特征A（SSE流式传输）与EP3812049A1的状态流式传输特征高度重合...”）。这绝非通用系统应有的行为。

## 2. 逻辑链条 (Logic Chain)

1. 根据用户指示，当前正在审查架构健壮性特性（熔断机制、Mock传输、参数处理器）是否真实动态实现。
2. 经查，在所谓“熔断后降级的 Mock 传输”（`_call_local_fallback_template`）中，系统不是在提供一个通用的兜底大模型方案或通用的拒绝服务机制，而是直接将**本次项目的完整测试剧本**写成了 `if-else` 的硬编码状态机。
3. `agentic_engine.py` 作为工作流引擎，理应具备处理任意专利 `claim` 的能力，但代码强行剥夺了 `claim` 的解析，直接赋予了针对本次特定测试用例的 `domestic_features` 和系统提示词。
4. `_argument_pre_processor` 名义上是参数清理，实际是针对特定测试用例的**硬编码参数覆盖**。
5. 上述所有发现表明，系统目前仍然是一个**专门为了通过该特定测试用例而编造的 Facade（门面）实现**，完全不具备真实的通用工作流处理能力，严重违反了 Demo Mode 下严禁 Hardcoded Test Results 和 Facade Implementations 的规则。

## 3. 局限性与前提假设 (Caveats)

- `tools/patent_tools.py` 中的专利库字典属于合理的“Mock 数据库”范畴（在非生产环境中可以接受），但这不能作为业务代码内部进行硬编码剧本、强制覆盖用户输入的借口。

## 4. 最终结论 (Conclusion)

系统未遵守“真实动态逻辑”的要求。之前发现的诸如“截断”、“Round 2”、“概率计算”等具体字符串虽然有形式上的改动，但实质上的硬编码剧本和“为测试用例量身定做的 Facade 实现”变本加厉。
这是一次**重大的完整性违规 (INTEGRITY VIOLATION)**。必须驳回。

## 5. 验证方法 (Verification Method)

- 直接查阅 `server/llm_factory.py` 的第 292 行至 646 行。
- 直接查阅 `server/agentic_engine.py` 的第 458 行、第 120 行、第 38 行。
- 这些代码包含了针对特定测试输入（SSE流式传输、多Agent辩论）的直接字符串响应和参数劫持，一目了然。
