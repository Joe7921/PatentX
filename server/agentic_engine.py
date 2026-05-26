# agentic_engine.py
# 基于模型主导的工具调用 (Function Calling) 与多层嵌套 Agent-as-Tool 的 ReAct 循环引擎

import asyncio
import json

import os
import yaml
import re
from typing import Dict, List, Any, Optional, AsyncGenerator, Callable, Awaitable

from blackboard import Blackboard
from tools.patent_tools import generate_feature_alignment_matrix
from llm_factory import LLMFactory
from mcp_client import MCPClientManager


def _sse(event_type: str, data: Dict[str, Any]) -> str:
    """格式化SSE事件字符串"""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _random_delay(low: float = 0.2, high: float = 0.5):
    """在指定范围内固定延迟，模拟Agent思考时间"""
    await asyncio.sleep((low + high) / 2)


def _load_agent_config(agent_name: str) -> Dict[str, Any]:
    """加载 app/agents/_custom/ 中的 Agent YAML 配置"""
    server_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(server_dir)
    config_path = os.path.join(project_dir, "app", "agents", "_custom", f"{agent_name}.yaml")
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _argument_pre_processor(tool_name: str, raw_args: Any, blackboard: Blackboard) -> Any:
    """统一的参数预处理器，负责对输入进行清洗和补全"""
    try:
        if isinstance(raw_args, str):
            tc_args = json.loads(raw_args)
        else:
            tc_args = raw_args
    except Exception:
        return "[ARGUMENT_PROCESSOR] Tool Error: Invalid JSON arguments"

    if not isinstance(tc_args, dict):
        return "[ARGUMENT_PROCESSOR] Tool Error: Arguments must be a JSON object"

    if tool_name == "generate_feature_alignment_matrix":
        required = ["domestic_feature_id", "domestic_feature", "prior_art_id", "prior_art_feature"]
        for req in required:
            if req not in tc_args:
                return f"[ARGUMENT_PROCESSOR] Tool Error: Missing required parameter '{req}'"
        
        # Keep the logging if it fixes simple formatting issues
        if "expert_annotations" not in tc_args or not isinstance(tc_args["expert_annotations"], str):
            print("[ARGUMENT_PROCESSOR] Auto-filling expert_annotations for generate_feature_alignment_matrix")
            tc_args["expert_annotations"] = json.dumps(getattr(blackboard, "expert_annotations", {}), ensure_ascii=False)

    return tc_args


# ====================================================================
# 投票倾向辅助函数及预置模板（仅在LLM动态生成投票异常时作为安全兜底）
# ====================================================================
async def _get_generic_vote_reasoning(voter: str, vote_decision: str, blackboard: Blackboard) -> str:
    fd_count = await blackboard.count_fully_disclosed()
    
    # 提取涉及的对比文献ID
    prior_arts = list(blackboard.feature_alignment_matrices.keys())
    pa_str = ", ".join(prior_arts) if prior_arts else "相关对比文献"

    if vote_decision == "Reject":
        return f"经过综合比对，有 {fd_count} 个核心特征被 {pa_str} 完全公开。申请人未能提供充分的技术证据证明其产生了不可预见的技术效果。整体方案缺乏新颖性。"
    elif vote_decision == "Conditional Grant":
        return f"有 {fd_count} 个核心特征被现有技术 {pa_str} 公开，存在部分新颖性问题，但未被公开的特征组合具有一定的技术创新性。建议附条件授权，要求申请人修改权利要求，将保护范围限缩至具有区别性的技术特征组合上。"
    else:
        return f"经过全面评估，本申请的技术方案在整体上与现有技术 {pa_str} 存在实质性区别。只有 {fd_count} 个特征被判定为完全公开，未被公开特征的有机结合产生了超出现有技术预期的协同技术效果，满足授权要求。"


def _determine_vote(agent_name: str, fully_disclosed_count: int) -> str:
    """基于 Fully_Disclosed 统计数确定投票倾向的随机倾向（确定性版本）"""
    import hashlib
    seed_str = f"{agent_name}_{fully_disclosed_count}"
    hash_val = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    rand_val = (hash_val % 10000) / 10000.0
    if fully_disclosed_count > 2:
        if rand_val < 0.75: return "Reject"
        elif rand_val < 0.95: return "Conditional Grant"
        else: return "Grant"
    elif fully_disclosed_count >= 1:
        if rand_val < 0.20: return "Reject"
        elif rand_val < 0.80: return "Conditional Grant"
        else: return "Grant"
    else:
        if rand_val < 0.05: return "Reject"
        elif rand_val < 0.20: return "Conditional Grant"
        else: return "Grant"


# ====================================================================
# 本地 Agent-as-Tool & HITL 声明 Schema
# ====================================================================
LOCAL_TOOLS_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "ask_epo_examiner",
            "description": "Consult the first EPO examiner for detailed technical or novelty objections about the patent claims.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The specific question or prompt for the examiner."}
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_second_examiner",
            "description": "Consult the second EPO examiner for their independent review comments or oral objections.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The specific question or prompt for the second examiner."}
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_patent_applicant",
            "description": "Consult the patent applicant or representative to defend the patent claims against objections.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The objections or questions to present to the applicant."}
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "request_human_expert",
            "description": "Suspend debate and ask a human expert to clarify or annotate a feature alignment dispute.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "The reason why human intervention is required."}
                },
                "required": ["reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "summon_legal_examiner",
            "description": "Summon a legal examiner to provide opinion on legal aspects or claim construction terms.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "The legal dispute or reason for summoning the legal examiner."}
                },
                "required": ["reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_legal_examiner",
            "description": "Consult the legal examiner to provide opinion on legal issues or EPC clauses.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The legal question or issue to address."}
                },
                "required": ["question"]
            }
        }
    }
]


# ====================================================================
# ReAct 运行期核心逻辑与黑板同步
# ====================================================================
async def _sync_search_results_to_blackboard(result_str: str, blackboard: Blackboard):
    try:
        data = json.loads(result_str)
        retrieved_patents = []
        for pid, pdata in data:
            claim_text = pdata.get("claim_1", "")
            if len(claim_text) > 200:
                claim_text = claim_text[:200] + "\n...[后部已截断]..."
            retrieved_patents.append({
                "id": pid,
                "title": pdata["title"],
                "patent_family": pdata["patent_family"],
                "claim_1": claim_text,
                "features": pdata["features"]
            })
        await blackboard.set_retrieved_patents(retrieved_patents)
    except Exception as e:
        print(f"[ERROR] Sync search results failed: {e}")


async def _sync_matrix_item_to_blackboard(prior_art_id: str, result_str: str, blackboard: Blackboard):
    if not prior_art_id:
        return
    try:
        item = json.loads(result_str)
        async with blackboard.lock:
            alignments = blackboard.feature_alignment_matrices.get(prior_art_id, [])
            df_id = item.get("domestic_feature_id")
            pf_id = item.get("prior_art_feature_id")
            
            updated = False
            for idx, existing in enumerate(alignments):
                if existing.get("domestic_feature_id") == df_id and existing.get("prior_art_feature_id") == pf_id:
                    alignments[idx] = item
                    updated = True
                    break
            if not updated:
                alignments.append(item)
            
            blackboard.feature_alignment_matrices[prior_art_id] = alignments
    except Exception as e:
        print(f"[ERROR] Sync matrix item failed: {e}")


async def execute_agent_react(
    agent_name: str,
    agent_role: str,
    phase_num: int,
    initial_user_msg: str,
    llm_client: Any,
    blackboard: Blackboard,
    yield_sse: Callable[[str, Dict[str, Any]], Awaitable[None]],
    local_tools_schemas: Optional[List[Dict[str, Any]]] = None,
    local_tools_dispatch: Optional[Dict[str, Any]] = None,
    max_rounds: int = 5,
    resume_event: Optional[asyncio.Event] = None,
    eval_id: str = ""
) -> str:
    """
    运行一个 Agent 的 ReAct 循环，支持 MCP 工具与本地自定义工具调用。
    每个动作都会输出相应的 SSE 事件。
    """
    config = _load_agent_config(agent_name)
    allowed_tools = config.get("tools", [])
    
    # 1. 连接 MCP Client 获取工具 Schema
    mcp_manager = await MCPClientManager.get_instance()
    mcp_schemas = await mcp_manager.get_tools_schema()
    
    tools = []
    for schema in mcp_schemas:
        if schema["function"]["name"] in allowed_tools:
            tools.append(schema)
            
    # 2. 注入本地 Tools 声明
    if local_tools_schemas:
        for schema in local_tools_schemas:
            if schema["function"]["name"] in allowed_tools:
                tools.append(schema)

    llm_tools = tools if tools else None

    # 3. 构造消息历史
    system_instruction = config.get("prompts", {}).get("system", "")
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": initial_user_msg})

    current_round = 1
    final_content = ""
    
    while current_round <= max_rounds:
        await blackboard.set_agent_state(agent_role, "thinking", "正在思考")
        response = await llm_client.chat(messages, tools=llm_tools)
        
        content = response.get("content")
        tool_calls = response.get("tool_calls")

        assistant_msg = {"role": "assistant"}
        if content:
            assistant_msg["content"] = content
        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls
        if response.get("reasoning_content"):
            assistant_msg["reasoning_content"] = response["reasoning_content"]
        messages.append(assistant_msg)

        # 处理 Thought / Content
        if content:
            final_content = content
            await blackboard.add_react_step(agent_role, phase_num, current_round, "think", content)
            await yield_sse("agent_think", {
                "type": "agent_think",
                "agent": agent_role,
                "phase": phase_num,
                "round": current_round,
                "content": content
            })
            await _random_delay()

        # 处理 Tool Call
        if tool_calls:
            for tool_call in tool_calls:
                tc_id = tool_call.get("id")
                tc_name = tool_call.get("function", {}).get("name")
                tc_args_str = tool_call.get("function", {}).get("arguments", "{}")
                
                tc_args = _argument_pre_processor(tc_name, tc_args_str, blackboard)
                
                is_error = isinstance(tc_args, str) and tc_args.startswith("[ARGUMENT_PROCESSOR] Tool Error")

                # 触发 agent_act
                act_msg = f"工具参数验证失败: {tc_name}" if is_error else f"正在调用工具 {tc_name}"
                await blackboard.add_react_step(agent_role, phase_num, current_round, "act", act_msg)
                await blackboard.set_agent_state(agent_role, "acting", f"调用 {tc_name}")
                await yield_sse("agent_act", {
                    "type": "agent_act",
                    "agent": agent_role,
                    "phase": phase_num,
                    "round": current_round,
                    "tool": tc_name,
                    "content": act_msg,
                    "tool_args": tc_args if not is_error else {}
                })
                await _random_delay()

                # 执行工具
                result_str = ""
                if is_error:
                    result_str = tc_args
                else:
                    if local_tools_dispatch and tc_name in local_tools_dispatch:
                        if tc_name == "request_human_expert":
                            result_str = await local_tools_dispatch[tc_name](tc_args.get("reason"), phase_num, resume_event, eval_id)
                        else:
                            if asyncio.iscoroutinefunction(local_tools_dispatch[tc_name]):
                                result_str = await local_tools_dispatch[tc_name](tc_args)
                            else:
                                result_str = local_tools_dispatch[tc_name](tc_args)
                    else:
                        result_str = await mcp_manager.call_tool(tc_name, tc_args)

                # 将工具执行结果记录为 observe 步骤并送回 LLM
                await blackboard.add_react_step(agent_role, phase_num, current_round, "observe", result_str)
                await blackboard.set_agent_state(agent_role, "observing", f"已获得 {tc_name} 结果")
                await yield_sse("agent_observe", {
                    "type": "agent_observe",
                    "agent": agent_role,
                    "phase": phase_num,
                    "round": current_round,
                    "content": result_str
                })
                
                # 同步到黑板
                if tc_name == "search_patent_db":
                    await _sync_search_results_to_blackboard(result_str, blackboard)
                elif tc_name == "generate_feature_alignment_matrix":
                    await _sync_matrix_item_to_blackboard(tc_args.get("prior_art_id"), result_str, blackboard)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "name": tc_name,
                    "content": result_str
                })
                await _random_delay()
                
            current_round += 1
        else:
            break

    return final_content


# ====================================================================
# 主工作流编排逻辑
# ====================================================================
async def run_workflow_logic(
    blackboard: Blackboard,
    claim: str,
    eval_id: str,
    resume_event: asyncio.Event,
    event_queue: asyncio.Queue
):
    async def yield_sse(event_type: str, data: Dict[str, Any]):
        await event_queue.put(_sse(event_type, data))

    # 动态解析国内特征 (Naively split claim by common punctuation)
    raw_features = re.split(r'[,;，；。且及与]+', claim)
    domestic_features = [f.strip() for f in raw_features if len(f.strip()) > 3]
    if not domestic_features:
        domestic_features = [claim]
    
    await blackboard.reset(eval_id, domestic_features)

    # 发送 node_start 事件
    await yield_sse("node_start", {
        "message": "Starting analysis...",
        "state": await blackboard.get_state()
    })

    # ----------------------------------------------------
    # Phase 1: 文档分析与检索
    # ----------------------------------------------------
    current_phase = 1
    await blackboard.set_phase(current_phase, "document_analysis")
    await blackboard.set_step("document_analysis")
    await blackboard.set_agent_state("first_examiner", "active")
    await yield_sse("phase_start", {
        "type": "phase_start",
        "phase": current_phase,
        "name": "document_analysis",
        "title": "文档分析与检索",
        "agents": ["first_examiner"]
    })
    await asyncio.sleep(1.0)

    fe_config = _load_agent_config("epo_examiner")
    fe_llm = LLMFactory.get_client("first_examiner", fe_config.get("llm", {}), blackboard)

    fe_initial_prompt = (
        f"Please analyze this patent claim: {claim}. Search the database to retrieve prior art patents, "
        f"and call the `generate_feature_alignment_matrix` tool to build the feature alignment matrix comparing each prior art feature to the domestic features: {json.dumps(domestic_features, ensure_ascii=False)}.\n"
        f"CRITICAL RULE: You MUST use IDs like 'DF_0', 'DF_1' etc for `domestic_feature_id`, corresponding to the index of each feature in the list. "
        f"Summarize your final findings."
    )
    
    await execute_agent_react(
        agent_name="epo_examiner",
        agent_role="first_examiner",
        phase_num=current_phase,
        initial_user_msg=fe_initial_prompt,
        llm_client=fe_llm,
        blackboard=blackboard,
        yield_sse=yield_sse,
        max_rounds=3
    )

    await blackboard.set_agent_state("first_examiner", "idle")
    fully_disclosed_count = await blackboard.count_fully_disclosed()
    phase1_summary = f"文档分析完成，检索到 {len(blackboard.retrieved_patents)} 件潜在冲突现有技术，{fully_disclosed_count} 个特征被判定为 Fully_Disclosed"
    await yield_sse("phase_complete", {
        "type": "phase_complete",
        "phase": current_phase,
        "summary": phase1_summary
    })
    await asyncio.sleep(1.0)

    # ----------------------------------------------------
    # Phase 2: 内部审查会议
    # ----------------------------------------------------
    current_phase = 2
    await blackboard.set_phase(current_phase, "internal_review")
    await blackboard.set_step("internal_review")
    await blackboard.set_agent_state("second_examiner", "active")
    await blackboard.set_agent_state("chairman", "active")
    await yield_sse("phase_start", {
        "type": "phase_start",
        "phase": current_phase,
        "name": "internal_review",
        "title": "内部审查会议",
        "agents": ["second_examiner", "chairman"]
    })
    await asyncio.sleep(1.0)

    # 定义 Judge 的本地嵌套 sub-agent 工具
    async def ask_epo_examiner_dispatch(args: Dict[str, Any]) -> str:
        question = args.get("question")
        se_config = _load_agent_config("epo_examiner")
        se_llm = LLMFactory.get_client("second_examiner", se_config.get("llm", {}), blackboard)
        ans = await execute_agent_react(
            agent_name="epo_examiner",
            agent_role="second_examiner",
            phase_num=current_phase,
            initial_user_msg=f"Please provide your independent review or reply to: {question}",
            llm_client=se_llm,
            blackboard=blackboard,
            yield_sse=yield_sse,
            max_rounds=2
        )
        await blackboard.add_debate_log(f"第二审查员发言: {ans}")
        return ans

    async def ask_patent_applicant_dispatch(args: Dict[str, Any]) -> str:
        question = args.get("question")
        ap_config = _load_agent_config("patent_applicant")
        ap_llm = LLMFactory.get_client("applicant_representative", ap_config.get("llm", {}), blackboard)
        ans = await execute_agent_react(
            agent_name="patent_applicant",
            agent_role="applicant_representative",
            phase_num=current_phase,
            initial_user_msg=f"Please reply and defend against: {question}",
            llm_client=ap_llm,
            blackboard=blackboard,
            yield_sse=yield_sse,
            max_rounds=2
        )
        await blackboard.add_debate_log(f"申请人代表发言: {ans}")
        return ans

    async def request_human_expert_dispatch(reason: str, phase_num: int, resume_event: asyncio.Event, eval_id: str) -> str:
        await blackboard.set_step("hitl_interrupted")
        await yield_sse("hitl_interrupt", {
            "type": "hitl_interrupt",
            "id": eval_id,
            "reason": reason,
            "phase": phase_num
        })
        await blackboard.add_debate_log(f"HITL中断: {reason}")
        try:
            await resume_event.wait()
        except asyncio.CancelledError:
            return "Expert session cancelled."
        
        await blackboard.set_step("internal_review" if phase_num == 2 else "oral_proceedings")
        await blackboard.add_debate_log("专家决策已导入黑板，重新评估特征对齐矩阵。")
        
        retrieved_patents = blackboard.retrieved_patents
        domestic_features = blackboard.claim_features
        for pdata in retrieved_patents:
            pid = pdata["id"]
            alignments = []
            for idx, df in enumerate(domestic_features):
                df_id = f"DF_{idx}"
                for pf in pdata["features"]:
                    matrix_item = generate_feature_alignment_matrix(
                        df_id, df, pid, pf, blackboard.expert_annotations
                    )
                    alignments.append(matrix_item)
            await blackboard.update_matrix(pid, alignments)
            
        se_config = _load_agent_config("epo_examiner")
        se_llm = LLMFactory.get_client("second_examiner", se_config.get("llm", {}), blackboard)
        se_ans = await execute_agent_react(
            agent_name="epo_examiner",
            agent_role="second_examiner",
            phase_num=phase_num,
            initial_user_msg="Expert annotations have been applied. Please provide your updated review (Round 2).",
            llm_client=se_llm,
            blackboard=blackboard,
            yield_sse=yield_sse,
            max_rounds=2
        )
        await blackboard.add_debate_log(f"审查员 (Round 2): {se_ans}")

        ap_config = _load_agent_config("patent_applicant")
        ap_llm = LLMFactory.get_client("applicant_representative", ap_config.get("llm", {}), blackboard)
        ap_ans = await execute_agent_react(
            agent_name="patent_applicant",
            agent_role="applicant_representative",
            phase_num=phase_num,
            initial_user_msg="Expert annotations have been applied. Please provide your updated defense (Round 2).",
            llm_client=ap_llm,
            blackboard=blackboard,
            yield_sse=yield_sse,
            max_rounds=2
        )
        await blackboard.add_debate_log(f"申请人代理 (Round 2): {ap_ans}")
            
        return f"Expert annotations applied. Updated fully disclosed features count: {await blackboard.count_fully_disclosed()}"

    async def summon_legal_examiner_dispatch(args: Dict[str, Any]) -> str:
        reason = args.get("reason")
        await blackboard.set_legal_examiner_summoned(True)
        await yield_sse("agent_summon", {
            "type": "agent_summon",
            "agent": "legal_examiner",
            "reason": reason
        })
        await blackboard.add_debate_log(f"法律审查员被召唤: {reason}")
        return f"Legal examiner summoned successfully for reason: {reason}"

    async def ask_legal_examiner_dispatch(args: Dict[str, Any]) -> str:
        if not await blackboard.is_legal_examiner_summoned():
            return "Error: Legal examiner has not been summoned yet."
        question = args.get("question")
        le_config = _load_agent_config("patent_judge")
        le_llm = LLMFactory.get_client("legal_examiner", le_config.get("llm", {}), blackboard)
        ans = await execute_agent_react(
            agent_name="patent_judge",
            agent_role="legal_examiner",
            phase_num=current_phase,
            initial_user_msg=f"Please provide your legal opinion on: {question}",
            llm_client=le_llm,
            blackboard=blackboard,
            yield_sse=yield_sse,
            max_rounds=2
        )
        await blackboard.add_debate_log(f"法律审查员发言: {ans}")
        return ans

    async def ask_second_examiner_dispatch(args: Dict[str, Any]) -> str:
        question = args.get("question")
        se_config = _load_agent_config("epo_examiner")
        se_llm = LLMFactory.get_client("second_examiner", se_config.get("llm", {}), blackboard)
        ans = await execute_agent_react(
            agent_name="epo_examiner",
            agent_role="second_examiner",
            phase_num=current_phase,
            initial_user_msg=f"Please provide your independent review, comments or reply to: {question}",
            llm_client=se_llm,
            blackboard=blackboard,
            yield_sse=yield_sse,
            max_rounds=2
        )
        await blackboard.add_debate_log(f"第二审查员发言: {ans}")
        return ans

    local_tools_dispatch = {
        "ask_epo_examiner": ask_epo_examiner_dispatch,
        "ask_second_examiner": ask_second_examiner_dispatch,
        "ask_patent_applicant": ask_patent_applicant_dispatch,
        "request_human_expert": lambda r, p, re, eid: request_human_expert_dispatch(r, current_phase, re, eid),
        "summon_legal_examiner": summon_legal_examiner_dispatch,
        "ask_legal_examiner": ask_legal_examiner_dispatch
    }

    ch_config = _load_agent_config("patent_judge")
    ch_llm = LLMFactory.get_client("chairman", ch_config.get("llm", {}), blackboard)

    patents_summary = json.dumps(blackboard.retrieved_patents, ensure_ascii=False)
    matrix_summary = json.dumps(blackboard.feature_alignment_matrices, ensure_ascii=False)
    
    ch_initial_prompt = f"You are the Patent Judge. The first examiner has completed the search. The retrieved patents are: {patents_summary}. The feature alignment matrix is: {matrix_summary}. Please coordinate the internal review. You MUST call `ask_epo_examiner` to get the second examiner's review. If there is a dispute or Fully_Disclosed feature count > 0, you can call `request_human_expert` to trigger HITL review. Decide if we need to summon the legal examiner using `summon_legal_examiner`. Provide your final summary when done."

    await execute_agent_react(
        agent_name="patent_judge",
        agent_role="chairman",
        phase_num=current_phase,
        initial_user_msg=ch_initial_prompt,
        llm_client=ch_llm,
        blackboard=blackboard,
        yield_sse=yield_sse,
        local_tools_schemas=LOCAL_TOOLS_SCHEMAS,
        local_tools_dispatch=local_tools_dispatch,
        max_rounds=4,
        resume_event=resume_event,
        eval_id=eval_id
    )

    await blackboard.set_agent_state("second_examiner", "idle")
    await blackboard.set_agent_state("chairman", "idle")
    fully_disclosed_count = await blackboard.count_fully_disclosed()
    legal_status = "已召唤法律审查员" if await blackboard.is_legal_examiner_summoned() else "未召唤法律审查员"
    phase2_summary = f"内部审查会议完成。Fully_Disclosed: {fully_disclosed_count}。{legal_status}。"
    await yield_sse("phase_complete", {
        "type": "phase_complete",
        "phase": current_phase,
        "summary": phase2_summary
    })
    await asyncio.sleep(1.0)

    # ----------------------------------------------------
    # Phase 3: 口头审理
    # ----------------------------------------------------
    current_phase = 3
    legal_summoned = await blackboard.is_legal_examiner_summoned()
    phase3_agents = ["first_examiner", "second_examiner", "chairman", "applicant_representative"]
    if legal_summoned:
        phase3_agents.append("legal_examiner")

    await blackboard.set_phase(current_phase, "oral_proceedings")
    await blackboard.set_step("oral_proceedings")
    for ag in phase3_agents:
        await blackboard.set_agent_state(ag, "active")

    await yield_sse("phase_start", {
        "type": "phase_start",
        "phase": current_phase,
        "name": "oral_proceedings",
        "title": "口头审理",
        "agents": phase3_agents
    })
    await asyncio.sleep(1.0)

    local_tools_dispatch["request_human_expert"] = lambda r, p, re, eid: request_human_expert_dispatch(r, current_phase, re, eid)

    ch_oral_prompt = f"You are the Patent Judge. Open and coordinate the oral hearing for patent claim: {claim}. Conduct the adversarial debate. You MUST: (1) Ask the first examiner (using `ask_epo_examiner`) to present their retrieval objections. (2) Ask the second examiner (using `ask_second_examiner`) to present their review. (3) Ask the applicant (using `ask_patent_applicant`) to defend. (4) If legal examiner is summoned (current status: {legal_summoned}), consult them using `ask_legal_examiner`. Provide your final summary of the hearing."

    await execute_agent_react(
        agent_name="patent_judge",
        agent_role="chairman",
        phase_num=current_phase,
        initial_user_msg=ch_oral_prompt,
        llm_client=ch_llm,
        blackboard=blackboard,
        yield_sse=yield_sse,
        local_tools_schemas=LOCAL_TOOLS_SCHEMAS,
        local_tools_dispatch=local_tools_dispatch,
        max_rounds=5,
        resume_event=resume_event,
        eval_id=eval_id
    )

    for ag in phase3_agents:
        await blackboard.set_agent_state(ag, "idle")

    await yield_sse("phase_complete", {
        "type": "phase_complete",
        "phase": current_phase,
        "summary": "口头审理完成，各方已充分陈述意见，准备进入最终投票阶段。"
    })
    await asyncio.sleep(1.0)

    # ----------------------------------------------------
    # Phase 4: 最终裁决
    # ----------------------------------------------------
    current_phase = 4
    voters = ["first_examiner", "second_examiner", "chairman"]
    if legal_summoned:
        voters.append("legal_examiner")

    await blackboard.set_phase(current_phase, "final_decision")
    await blackboard.set_step("final_decision")
    for v in voters:
        await blackboard.set_agent_state(v, "voting")

    await yield_sse("phase_start", {
        "type": "phase_start",
        "phase": current_phase,
        "name": "final_decision",
        "title": "最终裁决",
        "agents": voters
    })
    await asyncio.sleep(1.0)

    vote_results = []
    debate_logs_str = "\n".join(blackboard.debate_logs)
    matrix_str = json.dumps(blackboard.feature_alignment_matrices, ensure_ascii=False)

    for voter in voters:
        if voter in ("first_examiner", "second_examiner"):
            v_config = _load_agent_config("epo_examiner")
        elif voter in ("chairman", "legal_examiner"):
            v_config = _load_agent_config("patent_judge")
            
        v_llm = LLMFactory.get_client(voter, v_config.get("llm", {}), blackboard)
        
        if voter == "chairman":
            system_instruction = f"You are {voter} in the patent examination board. You must cast your vote: Grant, Reject, or Conditional Grant, based on the debate log and the feature alignment matrix. Output only a JSON object matching the format: {{\"vote\": \"Grant|Reject|Conditional Grant\", \"reasoning\": \"Your reasoning\", \"probability\": 0.95}}"
        else:
            system_instruction = f"You are {voter} in the patent examination board. You must cast your vote: Grant, Reject, or Conditional Grant, based on the debate log and the feature alignment matrix. Output only a JSON object matching the format: {{\"vote\": \"Grant|Reject|Conditional Grant\", \"reasoning\": \"Your reasoning\"}}"
        prompt = f"Here is the complete debate history:\n{debate_logs_str}\n\nHere is the final feature alignment matrix:\n{matrix_str}\n\nPlease cast your vote in JSON."
        
        try:
            resp = await v_llm.generate(prompt, system_instruction=system_instruction)
            content = resp.get("content", "")
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            parsed = json.loads(content)
            vote_decision = parsed.get("vote", "Reject")
            vote_reasoning = parsed.get("reasoning", "No reasoning provided.")
            if voter == "chairman":
                blackboard.chairman_probability = parsed.get("probability", 0.0)
        except Exception as e:
            print(f"[WARNING] Voter {voter} failed to vote dynamically: {e}. Falling back to default vote logic.")
            current_fd_count = await blackboard.count_fully_disclosed()
            vote_decision = _determine_vote(voter, current_fd_count)
            vote_reasoning = await _get_generic_vote_reasoning(voter, vote_decision, blackboard)
            if voter == "chairman":
                blackboard.chairman_probability = 0.95 if vote_decision == "Grant" else 0.0

        await blackboard.add_vote(voter, vote_decision, vote_reasoning)
        vote_results.append({
            "agent": voter,
            "vote": vote_decision,
            "reasoning": vote_reasoning
        })

        await yield_sse("vote_cast", {
            "type": "vote_cast",
            "agent": voter,
            "vote": vote_decision,
            "reasoning": vote_reasoning
        })
        await asyncio.sleep(1.5)

    # 汇总选票
    vote_counts = {"Grant": 0, "Reject": 0, "Conditional Grant": 0}
    for vr in vote_results:
        vote_counts[vr["vote"]] += 1

    majority_vote = max(vote_counts, key=vote_counts.get)
    total_voters = len(vote_results)

    probability = getattr(blackboard, "chairman_probability", 0.0)

    if majority_vote == "Grant":
        conclusion = f"经 {total_voters} 名审查员投票，多数决定授予专利权。本申请的技术方案在整体上具有足够的新颖性和创造性贡献，满足EPC授权标准。投票结果：Grant {vote_counts['Grant']} 票，Conditional Grant {vote_counts['Conditional Grant']} 票，Reject {vote_counts['Reject']} 票。"
    elif majority_vote == "Conditional Grant":
        conclusion = f"经 {total_voters} 名审查员投票，多数决定附条件授权。申请人需根据审查意见修改权利要求书，限缩保护范围至真正具有新颖性的技术特征组合。投票结果：Grant {vote_counts['Grant']} 票，Conditional Grant {vote_counts['Conditional Grant']} 票., Reject {vote_counts['Reject']} 票。"
    else:
        conclusion = f"经 {total_voters} 名审查员投票，多数决定驳回申请。本申请的核心技术方案在新颖性方面存在重大缺陷，多项关键技术特征已被现有技术公开。投票结果：Grant {vote_counts['Grant']} 票，Conditional Grant {vote_counts['Conditional Grant']} 票，Reject {vote_counts['Reject']} 票。"

    await blackboard.set_conclusion(probability, conclusion)
    await blackboard.add_debate_log(f"最终裁决: {conclusion}")

    for v in voters:
        await blackboard.set_agent_state(v, "idle")

    await yield_sse("phase_complete", {
        "type": "phase_complete",
        "phase": current_phase,
        "summary": f"最终裁决完成。多数票: {majority_vote}。EPO授权概率: {probability * 100:.0f}%。"
    })
    await _random_delay()

    await blackboard.set_step("completed")
    state = await blackboard.get_state()
    await yield_sse("completed", {
        "type": "completed",
        "conclusion": conclusion,
        "probability": probability,
        "votes": vote_results,
        "state": state
    })


async def run_agentic_workflow(
    blackboard: Blackboard,
    claim: str,
    eval_id: str,
    resume_event: asyncio.Event
) -> AsyncGenerator[str, None]:
    """
    4阶段EPO审查工作流的核心异步生成器。
    通过事件队列的形式，完美解耦 nested tool calling 与 SSE 异步流输出。
    """
    event_queue = asyncio.Queue()
    
    # 启动工作流后台任务
    workflow_task = asyncio.create_task(run_workflow_logic(blackboard, claim, eval_id, resume_event, event_queue))
    
    try:
        while not workflow_task.done() or not event_queue.empty():
            try:
                # 轮询获取 SSE 事件
                event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                yield event
            except asyncio.TimeoutError:
                continue
                
        # 确保后台任务异常能够抛出
        if workflow_task.done():
            workflow_task.result()
            
    except asyncio.CancelledError:
        workflow_task.cancel()
        raise
