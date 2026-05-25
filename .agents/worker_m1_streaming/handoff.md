# Handoff Report — M1 后端 Agentic SSE 引擎实现

## Observation

### 修改和新建的文件

| 文件 | 操作 | 行数 | 说明 |
|------|------|------|------|
| `server/agentic_engine.py` | **新建** | 734行 | 4阶段EPO审查工作流的核心Agentic SSE引擎 |
| `server/main.py` | **修改** | 165行(原379行) | 重写analyze_stream，委托给agentic_engine |
| `server/blackboard.py` | **未修改** | 188行 | 已有所有需要的扩展字段和方法 |
| `server/llm_factory.py` | **未修改** | 136行 | 保持不变 |
| `tools/patent_tools.py` | **未修改** | 153行 | 保持不变 |

### 新文件 `server/agentic_engine.py` 核心结构

- `_sse()` — 格式化SSE事件字符串
- `_random_delay()` — 随机延迟(0.3-0.8s)
- `_try_llm_generate()` — LLM调用 + fallback模拟文本
- `_load_agent_config()` — 加载Agent YAML配置
- `_determine_vote()` — 基于Fully_Disclosed计数的投票逻辑（含随机性）
- `run_agentic_workflow()` — 核心4阶段异步生成器

### `main.py` 修改范围

- 第19-22行: 增加 `from agentic_engine import run_agentic_workflow` 导入
- 第88-120行: `analyze_stream` 函数简化为委托给 `run_agentic_workflow`
- 第127-165行: `/resume` 和 `/blackboard` 端点完全保留不变

## Logic Chain

1. **blackboard.py 已有扩展字段**：检查发现 `current_phase`, `react_history`, `votes`, `legal_examiner_summoned` 及其 setter/getter 已存在（lines 24-166），无需修改。

2. **agentic_engine.py 实现4阶段工作流**：
   - Phase 1 (document_analysis): 仅 `first_examiner` 参与，2轮ReAct循环（Think→Act→Observe），实际调用 `search_patent_db` 和 `generate_feature_alignment_matrix`
   - Phase 2 (internal_review): `second_examiner` 独立复核 + `chairman` 审阅决策。如Fully_Disclosed≥1，召唤legal_examiner（`agent_summon`事件）并触发HITL中断
   - Phase 3 (oral_proceedings): 4个主要agent + 可选legal_examiner参与对抗辩论
   - Phase 4 (final_decision): 3-4人投票，基于Fully_Disclosed计数的概率化投票逻辑

3. **LLM降级策略**：`_try_llm_generate()` 先尝试真实LLM，失败则返回预写的高质量中文模拟文本。模拟文本按角色差异化：审查员严谨、申请人辩护、主席中立、法律审查员引用EPC条款。

4. **SSE事件协议严格遵守**：所有事件格式为 `event: <type>\ndata: {JSON}\n\n`，事件类型包括: `phase_start`, `agent_think`, `agent_act`, `agent_observe`, `phase_complete`, `agent_summon`, `hitl_interrupt`, `vote_cast`, `completed`

5. **resume端点保持正常**：main.py中 `/api/v1/evaluation/{id}/resume` (lines 127-157) 和 `/api/v1/evaluation/{id}/blackboard` (lines 159-165) 完全未修改。resume_event 通过参数传递给 agentic_engine，在Phase 2的HITL中断处等待。

6. **投票逻辑**：`_determine_vote()` 基于Fully_Disclosed计数:
   - >2: 75%Reject, 20%Conditional, 5%Grant
   - 1-2: 20%Reject, 60%Conditional, 20%Grant
   - 0: 5%Reject, 15%Conditional, 80%Grant

7. **时间间隔**：
   - 每个SSE事件之间: `_random_delay(0.3, 0.8)`
   - 投票之间: `asyncio.sleep(1.5)`
   - 阶段之间: `asyncio.sleep(1.0)`

## Caveats

1. **命令执行未获批准**：用户未在超时窗口内批准 `python -c "import sys; sys.path.insert(0,'server'); from main import app; print('Backend import OK')"` 命令。导入验证基于静态代码分析完成，未能运行实际测试。
2. **LLM调用**：在没有配置 `DEEPSEEK_API_KEY` 的环境中，所有LLM调用都会fallback到预写模拟文本。这是设计意图。
3. **默认claim文本**：默认claim "一种嵌套多Agent协作与流式状态同步挂起的智能专利检索及评估系统，且具有安全验证恢复机制" 会匹配到两个模拟专利(EP3812049A1, EP4012055A2)，产生多个Fully_Disclosed，从而触发legal_examiner召唤和HITL中断。

## Conclusion

M1任务已完成。创建了 `server/agentic_engine.py` (734行) 实现4阶段EPO审查工作流，重写了 `server/main.py` 的 `analyze_stream` 函数委托给新引擎。所有SSE事件协议、Agent参与规则、投票逻辑和HITL中断机制均按规范实现。保持了 `/resume` 和 `/blackboard` 端点不变。

## Verification Method

运行以下命令验证无导入错误:
```powershell
cd "d:\Antigravity projects\PatentX" ; python -c "import sys; sys.path.insert(0,'server'); from main import app; print('Backend import OK')"
```

验证SSE事件序列（启动服务后用curl测试）:
```powershell
cd "d:\Antigravity projects\PatentX\server" ; python -m uvicorn main:app --host 127.0.0.1 --port 8000
# 另一个终端:
# curl http://127.0.0.1:8000/api/v1/analyze/stream
```

预期事件序列:
1. `phase_start` (phase=1, agents=["first_examiner"])
2. `agent_think` → `agent_act` → `agent_observe` (round 1)
3. `agent_think` → `agent_act` → `agent_observe` (round 2)
4. `phase_complete` (phase=1)
5. `phase_start` (phase=2, agents=["second_examiner","chairman"])
6. `agent_think` → `agent_observe` (second_examiner)
7. `agent_think` (chairman)
8. `agent_summon` (legal_examiner) — 如有法律争议
9. `hitl_interrupt` — 如Fully_Disclosed > 0
10. `phase_complete` (phase=2) — resume后
11. `phase_start` (phase=3, agents=["first_examiner","second_examiner","chairman","applicant_representative"(,"legal_examiner")])
12. 多个 `agent_think` / `agent_observe` 事件
13. `phase_complete` (phase=3)
14. `phase_start` (phase=4, agents=[voters])
15. 3-4个 `vote_cast` 事件
16. `phase_complete` (phase=4)
17. `completed` (含conclusion, probability, votes, state)
