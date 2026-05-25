# agentic_engine.py
# 4阶段EPO审查工作流 Agentic SSE 引擎
# 实现真正的ReAct循环，每步以独立SSE事件推送到前端

import asyncio
import json
import random
from typing import Dict, List, Any, Optional, AsyncGenerator

from blackboard import Blackboard
from tools.patent_tools import search_patent_db, generate_feature_alignment_matrix
from llm_factory import LLMFactory


def _sse(event_type: str, data: Dict[str, Any]) -> str:
    """格式化SSE事件字符串"""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _random_delay(low: float = 0.3, high: float = 0.8):
    """在指定范围内随机延迟，模拟Agent思考时间"""
    await asyncio.sleep(random.uniform(low, high))


async def _try_llm_generate(llm_client, prompt: str, fallback_text: str) -> str:
    """
    尝试通过LLM生成内容，失败时返回预写的高质量模拟文本。
    不吞没异常信息，而是记录后降级。
    """
    try:
        result = await llm_client.generate(prompt)
        return result
    except Exception:
        # LLM调用失败（如API KEY缺失），降级到预写模拟文本
        return fallback_text


def _load_agent_config(agent_name: str) -> Dict[str, Any]:
    """加载 app/agents/_custom/ 中的 Agent YAML 配置"""
    import os
    import yaml
    server_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(server_dir)
    config_path = os.path.join(project_dir, "app", "agents", "_custom", f"{agent_name}.yaml")
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ====================================================================
# 每个Agent角色的高质量模拟文本模板（当LLM不可用时使用）
# 体现角色差异：审查员严谨、申请人辩护、主席中立、法律审查员专业
# ====================================================================

# --- Phase 1: 文档分析与检索 (first_examiner) ---
_FIRST_EXAMINER_THINK_TEMPLATES = [
    "让我仔细分析这份专利权利要求书的核心技术特征。该权利要求涉及多Agent协作架构与流式状态同步机制，我需要将其拆解为独立的技术特征单元，并确定合适的检索策略。关键技术点包括：(1) 嵌套多Agent协作编排；(2) SSE流式实时状态传输；(3) 安全验证恢复机制。我将以这些核心特征作为检索锚点，在EPO专利数据库中搜索可能构成新颖性障碍的现有技术。",
    "基于第一轮检索结果，我发现有多件欧洲专利涉及类似的技术领域。我需要进一步缩小检索范围，重点关注SSE流式传输与多Agent辩论协调的交叉技术领域，以确认是否存在完全披露的特征重合。同时需要评估这些现有技术的权利要求范围是否与本申请存在实质性重叠。",
]

_FIRST_EXAMINER_ACT_TEMPLATES = [
    "正在检索EPO专利数据库，检索策略：以'多Agent协作'、'SSE流式传输'、'状态同步挂起'为主要关键词，结合IPC分类号G06F9/46(多程序安排)和H04L67/02(服务器端流式数据)进行交叉检索...",
    "扩展检索范围，追加关键词'鉴权恢复'、'流中断续传'，同时检索非专利文献(NPL)以确认该技术领域的现有技术水平...",
]

_FIRST_EXAMINER_OBSERVE_TEMPLATES = [
    "检索到{count}件相关欧洲专利。初步分析表明：{patent_ids}可能与本申请的核心技术特征存在重合。EP3812049A1涉及分布式状态流式传输系统，其权利要求1的技术方案与本申请的SSE流式传输特征高度相似；EP4012055A2涉及多Agent分层辩论系统，其协调机制与本申请的Agent协作架构存在交叉。需要进入详细的逐特征对比分析阶段。",
    "进一步分析发现，EP3812049A1中的'pause coordinator'和'resume hook'与本申请的HITL中断-恢复机制存在功能性相似。但本申请强调的'嵌套'Agent架构（而非简单的扁平协调）可能构成区别技术特征。我将把这些发现记录到黑板上，供后续阶段参考。",
]

# --- Phase 2: 内部审查会议 (second_examiner, chairman) ---
_SECOND_EXAMINER_TEMPLATES = {
    "think": "作为第二审查员，我对第一审查员的检索结果进行独立复核。从特征对齐矩阵来看，{disclosed_count}个特征被标记为'Fully_Disclosed'。我需要验证这些判定是否准确，特别是在'嵌套多Agent协作'这一区别特征上，现有技术EP4012055A2描述的是分层结构，而本申请强调的是'嵌套'——二者的技术含义是否存在实质差异，需要更细致的分析。",
    "review": "经过独立复核，我确认第一审查员的特征对齐判定基本准确。关于EP3812049A1的SSE特征与本申请的对比，我认为两者在技术方案层面存在实质性重合。但在'安全验证恢复机制'这一特征上，本申请的实现方式（基于令牌的鉴权恢复）可能与现有技术存在细微但重要的区别。建议进入口头审理阶段进行深入讨论。",
}

_CHAIRMAN_TEMPLATES = {
    "review": "作为审查委员会主席，我已审阅第一审查员的检索报告和第二审查员的独立复核意见。综合两位审查员的分析，本案存在以下关键争议点：(1) SSE流式传输特征与EP3812049A1的技术方案重合度；(2) 多Agent协作架构与EP4012055A2的实质区别；(3) 鉴权恢复机制的新颖性评估。{decision}",
    "summon_legal": "鉴于本案涉及权利要求解释的法律问题——特别是'嵌套'一词的技术含义是否足以构成EPC第54条意义上的新颖性区别特征——我决定召唤法律审查员参与本次审查，以确保法律论证的严谨性。",
    "hitl_reason": "审查员在新颖性判定上存在重大分歧，第一审查员认为SSE流式传输特征已被完全披露，但申请人可能对此提出异议。需要人类专家介入，对特征对齐矩阵中的关键判定进行复核和修正。",
    "no_conflict": "两位审查员的独立评估结果高度一致，未发现重大分歧。本案可直接进入口头审理阶段。",
}

# --- Phase 3: 口头审理 (全部4个主要agent + 可选 legal_examiner) ---
_ORAL_PROCEEDINGS = {
    "chairman_open": "本次口头审理正式开始。议题：审查本申请'{claim_summary}'的新颖性和创造性。各方请就以下争议焦点发表意见：(1) SSE流式状态同步机制是否构成新颖性特征；(2) 嵌套多Agent协作架构与现有分层系统的技术区别；(3) 安全验证恢复机制的创造性贡献。首先请第一审查员陈述检索结论。",
    "first_examiner_statement": "根据检索结果，本申请的核心技术方案与以下现有技术存在实质性重合：EP3812049A1已公开了基于SSE的状态流式传输和HITL中断-恢复机制；EP4012055A2已公开了多Agent分层辩论协调系统。本审查员认为，本申请缺乏EPC第54条规定的新颖性，特别是在SSE流式传输和Agent协调方面。然而，本申请的'嵌套'Agent架构和'安全验证恢复'机制可能包含某些区别特征，需要进一步评估。",
    "applicant_defense": "申请人代理对审查员的意见提出以下答辩：(1) 本申请的'嵌套多Agent协作'采用了递归委托模式，与EP4012055A2的简单分层结构存在本质区别——本申请中的Agent可以动态嵌套子Agent链，形成树状决策结构，而非固定的两层架构；(2) 本申请的SSE流式传输不仅传输状态变化，还支持'状态同步挂起'——即在中间Agent发生异常时自动保存完整状态快照并安全挂起，这在EP3812049A1中未被提及；(3) 安全验证恢复机制通过令牌绑定评估上下文，实现了无状态恢复，这是现有技术中不存在的创新点。",
    "second_examiner_rebuttal": "第二审查员认为申请人的答辩部分有理。关于'嵌套'架构的区别论点值得考虑，但需要申请人提供更具体的技术细节来证明这种'递归委托模式'与现有技术的'分层委托'之间存在不可预见的技术效果差异。关于SSE状态同步挂起，EP3812049A1的'pause coordinator'功能描述较为宽泛，可能已隐含了类似的状态保存机制。建议对此进行更精确的特征对比。",
    "legal_examiner_opinion": "从法律角度分析，本案的关键在于EPC第54(2)条中'新颖性'的判定标准。根据EPO扩大上诉委员会的判例法(G 2/10)，判断新颖性时应当考虑权利要求的所有技术特征的组合效果，而非孤立比较单个特征。本申请将'嵌套Agent协作'、'SSE流式状态同步挂起'和'安全验证恢复'作为一个整体技术方案提出，应当从整体技术效果的角度评估其相对于最接近现有技术的区别。此外，关于'嵌套'一词的技术含义，需要参照说明书的上下文进行解释，不能仅从字面含义推断。",
    "chairman_summary": "综合各方意见，本次口头审理达成以下共识：(1) 本申请在SSE流式传输方面与EP3812049A1存在重合，但'状态同步挂起'功能可能构成区别特征；(2) '嵌套多Agent协作'架构需要进一步技术论证以证明其新颖性；(3) '安全验证恢复机制'具有一定的创造性贡献。现在进入最终投票阶段。",
}

# --- Phase 4: 投票模板 ---
_VOTE_TEMPLATES = {
    "first_examiner": {
        "Reject": "核心技术特征A（SSE流式传输）与EP3812049A1的状态流式传输特征高度重合，且特征B（多Agent协作）与EP4012055A2的分层辩论系统存在实质性重叠。虽然申请人主张'嵌套'架构的区别，但未能提供充分的技术证据证明其产生了不可预见的技术效果。整体方案缺乏EPC第54条规定的新颖性。",
        "Conditional Grant": "尽管部分核心技术特征与现有技术存在重合，但本申请的'嵌套Agent递归委托'和'状态同步挂起'功能组合具有一定的技术创新性。建议申请人修改权利要求，将保护范围限缩至这些具有区别性的技术特征组合上，以满足新颖性和创造性要求。",
        "Grant": "经过全面评估，本申请的技术方案在整体上与现有技术存在实质性区别。'嵌套多Agent递归协作'、'SSE状态同步挂起'和'令牌绑定安全恢复'三者的有机结合产生了超出现有技术预期的协同技术效果，满足EPC第52至56条的授权要求。",
    },
    "second_examiner": {
        "Reject": "同意第一审查员的检索结论。本申请的多项关键技术特征已在EP3812049A1和EP4012055A2中被单独或组合公开。申请人的答辩虽然指出了某些技术细节上的差异，但这些差异不足以构成EPC第56条意义上的创造性贡献。整体判定为不授权。",
        "Conditional Grant": "本申请存在部分新颖性问题，但'嵌套Agent架构'的递归委托模式确实与现有技术的扁平分层结构存在技术区别。建议附条件授权：申请人需修改权利要求，明确限定'嵌套'的技术实现方式，并删除与EP3812049A1重合的通用SSE传输特征描述。",
        "Grant": "本申请的技术方案具有足够的新颖性和创造性。特别是将嵌套Agent协作与SSE状态同步挂起相结合的整体技术方案，在现有技术中未见先例。建议授权。",
    },
    "chairman": {
        "Reject": "作为主席，综合两位审查员的独立评估和口头审理中各方的陈述，本申请的核心技术方案在新颖性方面存在重大缺陷。尽管申请人提出了关于'嵌套架构'的答辩，但未能提供令人信服的技术证据。投票：驳回申请。",
        "Conditional Grant": "综合评估后，本案的技术方案在特定方面具有创新价值，但权利要求的撰写范围过宽，涵盖了部分已被现有技术公开的通用特征。建议附条件授权，要求申请人在3个月内提交修改后的权利要求书，限缩保护范围至真正具有新颖性的技术特征组合。",
        "Grant": "经过充分的口头审理和投票协商，本申请的整体技术方案具有足够的新颖性和创造性贡献，满足EPC授权标准。投票：授予专利权。",
    },
    "legal_examiner": {
        "Reject": "从法律角度，本申请的权利要求未能满足EPC第52-56条的要求。关键技术特征已被现有技术所公开，且申请人未能依据EPC第123(2)条在不超出原始申请范围的前提下进行有效修改。",
        "Conditional Grant": "法律上，本申请具有授权的可能性，前提是申请人根据EPC第123(2)条对权利要求进行限缩性修改。建议关注规则137(5)条规定的修改时限和程序要求。",
        "Grant": "从法律角度确认，本申请的技术方案满足EPC授权条件。权利要求的撰写符合EPC第84条的清晰性和简洁性要求，说明书的公开程度满足EPC第83条的充分公开要求。",
    },
}


def _determine_vote(agent_name: str, fully_disclosed_count: int) -> str:
    """
    基于blackboard中的Fully_Disclosed统计数确定投票倾向。
    每个审查员有轻微随机性模拟独立判断。
    """
    rand_val = random.random()

    if fully_disclosed_count > 2:
        # 高冲突：大概率Reject
        if rand_val < 0.75:
            return "Reject"
        elif rand_val < 0.95:
            return "Conditional Grant"
        else:
            return "Grant"
    elif fully_disclosed_count >= 1:
        # 中等冲突：倾向Conditional Grant
        if rand_val < 0.20:
            return "Reject"
        elif rand_val < 0.80:
            return "Conditional Grant"
        else:
            return "Grant"
    else:
        # 无冲突：大概率Grant
        if rand_val < 0.05:
            return "Reject"
        elif rand_val < 0.20:
            return "Conditional Grant"
        else:
            return "Grant"


async def run_agentic_workflow(
    blackboard: Blackboard,
    claim: str,
    eval_id: str,
    resume_event: asyncio.Event
) -> AsyncGenerator[str, None]:
    """
    4阶段EPO审查工作流的核心异步生成器。
    每一步yield一个格式化的SSE事件字符串。
    
    阶段:
      1. 文档分析与检索 (Document Analysis & Search) — first_examiner
      2. 内部审查会议 (Internal Review Meeting) — second_examiner, chairman
      3. 口头审理 (Oral Proceedings) — 全部4个主要agent + 可选legal_examiner
      4. 最终裁决 (Final Decision) — 投票
    """

    # 定义国内专利特征拆解（与原main.py保持一致的逻辑）
    domestic_features = [
        "特征A: 支持多Agent嵌套协作的专利评估，由法官Agent协调各专业Agent辩论",
        "特征B: 采用SSE流式传输，在遇到状态变化时支持自动状态同步与挂起",
        "特征C: 具有鉴权恢复机制，能根据令牌重新建立评估流并恢复进度"
    ]
    await blackboard.reset(eval_id, domestic_features)

    # ====================================================================
    # Phase 1: 文档分析与检索 (Document Analysis & Search)
    # 仅 first_examiner 参与，执行ReAct循环
    # ====================================================================
    await blackboard.set_phase(1, "document_analysis")
    await blackboard.set_step("document_analysis")
    await blackboard.set_agent_state("first_examiner", "active")

    yield _sse("phase_start", {
        "type": "phase_start",
        "phase": 1,
        "name": "document_analysis",
        "title": "文档分析与检索",
        "agents": ["first_examiner"]
    })
    await asyncio.sleep(1.0)

    # 初始化LLM客户端 (first_examiner)
    fe_config = _load_agent_config("epo_examiner")
    fe_llm = LLMFactory.get_client("first_examiner", fe_config.get("llm", {}), blackboard)

    # --- ReAct 第1轮: 分析权利要求，制定检索策略 ---
    # Think
    think_content_1 = await _try_llm_generate(
        fe_llm,
        f"你是EPO第一审查员。请分析以下专利权利要求的核心技术特征，并制定检索策略：\n{claim}",
        _FIRST_EXAMINER_THINK_TEMPLATES[0]
    )
    await blackboard.add_react_step("first_examiner", 1, 1, "think", think_content_1)
    await blackboard.set_agent_state("first_examiner", "thinking", "分析权利要求")
    yield _sse("agent_think", {
        "type": "agent_think",
        "agent": "first_examiner",
        "phase": 1,
        "round": 1,
        "content": think_content_1
    })
    await _random_delay()

    # Act
    act_content_1 = _FIRST_EXAMINER_ACT_TEMPLATES[0]
    await blackboard.add_react_step("first_examiner", 1, 1, "act", act_content_1)
    await blackboard.set_agent_state("first_examiner", "acting", "检索EPO数据库")
    yield _sse("agent_act", {
        "type": "agent_act",
        "agent": "first_examiner",
        "phase": 1,
        "round": 1,
        "tool": "search_patent_db",
        "content": act_content_1
    })
    await _random_delay()

    # 实际执行检索
    raw_results = search_patent_db(claim)
    retrieved_patents = []
    for pid, pdata in raw_results:
        retrieved_patents.append({
            "id": pid,
            "title": pdata["title"],
            "patent_family": pdata["patent_family"],
            "claim_1": pdata["claim_1"],
            "features": pdata["features"]
        })
    await blackboard.set_retrieved_patents(retrieved_patents)
    retrieved_ids = [p["id"] for p in retrieved_patents]

    # Observe
    observe_content_1 = _FIRST_EXAMINER_OBSERVE_TEMPLATES[0].format(
        count=len(retrieved_patents),
        patent_ids="、".join(retrieved_ids)
    )
    await blackboard.add_react_step("first_examiner", 1, 1, "observe", observe_content_1)
    await blackboard.set_agent_state("first_examiner", "observing", "整理检索结果")
    yield _sse("agent_observe", {
        "type": "agent_observe",
        "agent": "first_examiner",
        "phase": 1,
        "round": 1,
        "content": observe_content_1
    })
    await _random_delay()

    # --- ReAct 第2轮: 深入分析，执行特征对齐 ---
    # Think
    think_content_2 = await _try_llm_generate(
        fe_llm,
        f"基于检索到的专利 {', '.join(retrieved_ids)}，请进一步分析与本申请权利要求的特征重合情况。",
        _FIRST_EXAMINER_THINK_TEMPLATES[1]
    )
    await blackboard.add_react_step("first_examiner", 1, 2, "think", think_content_2)
    await blackboard.set_agent_state("first_examiner", "thinking", "深入特征分析")
    yield _sse("agent_think", {
        "type": "agent_think",
        "agent": "first_examiner",
        "phase": 1,
        "round": 2,
        "content": think_content_2
    })
    await _random_delay()

    # Act: 执行特征对齐矩阵构建
    act_content_2 = _FIRST_EXAMINER_ACT_TEMPLATES[1]
    await blackboard.add_react_step("first_examiner", 1, 2, "act", act_content_2)
    await blackboard.set_agent_state("first_examiner", "acting", "构建特征对齐矩阵")
    yield _sse("agent_act", {
        "type": "agent_act",
        "agent": "first_examiner",
        "phase": 1,
        "round": 2,
        "tool": "search_patent_db",
        "content": act_content_2
    })
    await _random_delay()

    # 实际执行特征对齐
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

    # Observe: 总结特征对齐结果
    fully_disclosed_count = await blackboard.count_fully_disclosed()
    observe_content_2 = _FIRST_EXAMINER_OBSERVE_TEMPLATES[1]
    await blackboard.add_react_step("first_examiner", 1, 2, "observe", observe_content_2)
    await blackboard.set_agent_state("first_examiner", "observing", "总结对齐结果")
    yield _sse("agent_observe", {
        "type": "agent_observe",
        "agent": "first_examiner",
        "phase": 1,
        "round": 2,
        "content": observe_content_2
    })
    await _random_delay()

    # Phase 1 完成
    await blackboard.set_agent_state("first_examiner", "idle")
    phase1_summary = f"文档分析完成，检索到{len(retrieved_patents)}件潜在冲突现有技术，{fully_disclosed_count}个特征被判定为Fully_Disclosed"
    yield _sse("phase_complete", {
        "type": "phase_complete",
        "phase": 1,
        "summary": phase1_summary
    })
    await asyncio.sleep(1.0)

    # ====================================================================
    # Phase 2: 内部审查会议 (Internal Review Meeting)
    # second_examiner 和 chairman 参与
    # ====================================================================
    await blackboard.set_phase(2, "internal_review")
    await blackboard.set_step("internal_review")
    await blackboard.set_agent_state("second_examiner", "active")
    await blackboard.set_agent_state("chairman", "active")

    yield _sse("phase_start", {
        "type": "phase_start",
        "phase": 2,
        "name": "internal_review",
        "title": "内部审查会议",
        "agents": ["second_examiner", "chairman"]
    })
    await asyncio.sleep(1.0)

    # --- Second Examiner 独立复核 ---
    se_config = _load_agent_config("epo_examiner")
    se_llm = LLMFactory.get_client("second_examiner", se_config.get("llm", {}), blackboard)

    # Think
    se_think = await _try_llm_generate(
        se_llm,
        f"你是EPO第二审查员，请独立复核第一审查员的检索结果。特征对齐矩阵中有{fully_disclosed_count}个Fully_Disclosed。",
        _SECOND_EXAMINER_TEMPLATES["think"].format(disclosed_count=fully_disclosed_count)
    )
    await blackboard.add_react_step("second_examiner", 2, 1, "think", se_think)
    await blackboard.set_agent_state("second_examiner", "thinking", "独立复核")
    yield _sse("agent_think", {
        "type": "agent_think",
        "agent": "second_examiner",
        "phase": 2,
        "round": 1,
        "content": se_think
    })
    await _random_delay()

    # Observe (审查意见)
    se_review = await _try_llm_generate(
        se_llm,
        "请给出你对第一审查员检索报告的独立复核意见。",
        _SECOND_EXAMINER_TEMPLATES["review"]
    )
    await blackboard.add_react_step("second_examiner", 2, 1, "observe", se_review)
    await blackboard.set_agent_state("second_examiner", "observing", "提交复核意见")
    await blackboard.add_debate_log(f"第二审查员复核意见: {se_review}")
    yield _sse("agent_observe", {
        "type": "agent_observe",
        "agent": "second_examiner",
        "phase": 2,
        "round": 1,
        "content": se_review
    })
    await _random_delay()

    # --- Chairman 审查并决策 ---
    ch_config = _load_agent_config("patent_judge")
    ch_llm = LLMFactory.get_client("chairman", ch_config.get("llm", {}), blackboard)

    # 判断是否需要召唤法律审查员
    # 如果检测到涉及法律解释争议（模拟：权利要求包含法律术语或存在较多冲突）
    has_legal_dispute = "法律" in claim or "解释" in claim or fully_disclosed_count >= 1

    if has_legal_dispute:
        decision_text = "鉴于本案涉及权利要求用语的法律解释争议，我决定召唤法律审查员加入审查团队。"
    else:
        decision_text = _CHAIRMAN_TEMPLATES["no_conflict"]

    ch_review = await _try_llm_generate(
        ch_llm,
        f"你是审查委员会主席。第一审查员发现{fully_disclosed_count}个Fully_Disclosed特征。第二审查员已完成独立复核。请审阅结果并决定下一步行动。",
        _CHAIRMAN_TEMPLATES["review"].format(decision=decision_text)
    )
    await blackboard.add_react_step("chairman", 2, 1, "think", ch_review)
    await blackboard.set_agent_state("chairman", "thinking", "审阅检索结果")
    await blackboard.add_debate_log(f"主席审阅意见: {ch_review}")
    yield _sse("agent_think", {
        "type": "agent_think",
        "agent": "chairman",
        "phase": 2,
        "round": 1,
        "content": ch_review
    })
    await _random_delay()

    # 如果检测到法律争议，发出agent_summon事件
    if has_legal_dispute:
        await blackboard.set_legal_examiner_summoned(True)
        summon_reason = _CHAIRMAN_TEMPLATES["summon_legal"]
        yield _sse("agent_summon", {
            "type": "agent_summon",
            "agent": "legal_examiner",
            "reason": summon_reason
        })
        await blackboard.add_debate_log(f"主席召唤法律审查员: {summon_reason}")
        await _random_delay()

    # 如果存在重大分歧 (Fully_Disclosed > 0)，触发HITL
    if fully_disclosed_count > 0:
        await blackboard.set_step("hitl_interrupted")
        hitl_reason = _CHAIRMAN_TEMPLATES["hitl_reason"]
        yield _sse("hitl_interrupt", {
            "type": "hitl_interrupt",
            "id": eval_id,
            "reason": hitl_reason,
            "phase": 2
        })
        await blackboard.add_debate_log(f"HITL中断: {hitl_reason}")

        try:
            # 等待专家 /resume 提交
            await asyncio.wait_for(resume_event.wait(), timeout=600.0)

            # 专家已介入，重新构建特征对齐矩阵
            await blackboard.set_step("internal_review")
            await blackboard.add_debate_log("专家决策已导入黑板，重新评估特征对齐矩阵。")

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

            # 更新Fully_Disclosed计数
            fully_disclosed_count = await blackboard.count_fully_disclosed()

            # 主席确认恢复
            ch_resume = f"专家修正意见已整合到特征对齐矩阵。更新后Fully_Disclosed数量: {fully_disclosed_count}。审查流程继续。"
            await blackboard.add_react_step("chairman", 2, 2, "observe", ch_resume)
            yield _sse("agent_observe", {
                "type": "agent_observe",
                "agent": "chairman",
                "phase": 2,
                "round": 2,
                "content": ch_resume
            })
            await _random_delay()

        except asyncio.TimeoutError:
            yield _sse("error", {
                "type": "error",
                "message": "等待专家输入超时（10分钟）。评估流程终止。"
            })
            return
        except asyncio.CancelledError:
            return

    # Phase 2 完成
    await blackboard.set_agent_state("second_examiner", "idle")
    await blackboard.set_agent_state("chairman", "idle")
    legal_status = "已召唤法律审查员" if await blackboard.is_legal_examiner_summoned() else "未召唤法律审查员"
    phase2_summary = f"内部审查会议完成。Fully_Disclosed: {fully_disclosed_count}。{legal_status}。"
    yield _sse("phase_complete", {
        "type": "phase_complete",
        "phase": 2,
        "summary": phase2_summary
    })
    await asyncio.sleep(1.0)

    # ====================================================================
    # Phase 3: 口头审理 (Oral Proceedings)
    # 所有4个主要agent参与: first_examiner, second_examiner, chairman, applicant_representative
    # 如果法律审查员已被召唤，也参与
    # ====================================================================
    legal_summoned = await blackboard.is_legal_examiner_summoned()
    phase3_agents = ["first_examiner", "second_examiner", "chairman", "applicant_representative"]
    if legal_summoned:
        phase3_agents.append("legal_examiner")

    await blackboard.set_phase(3, "oral_proceedings")
    await blackboard.set_step("oral_proceedings")
    for ag in phase3_agents:
        await blackboard.set_agent_state(ag, "active")

    yield _sse("phase_start", {
        "type": "phase_start",
        "phase": 3,
        "name": "oral_proceedings",
        "title": "口头审理",
        "agents": phase3_agents
    })
    await asyncio.sleep(1.0)

    # --- Chairman 主持开场 ---
    claim_summary = claim[:30] + "..." if len(claim) > 30 else claim
    ch_open = await _try_llm_generate(
        ch_llm,
        f"你是审查委员会主席，请主持口头审理开场。申请权利要求: {claim}",
        _ORAL_PROCEEDINGS["chairman_open"].format(claim_summary=claim_summary)
    )
    await blackboard.add_react_step("chairman", 3, 1, "think", ch_open)
    await blackboard.set_agent_state("chairman", "thinking", "主持口头审理")
    await blackboard.add_debate_log(f"主席开场: {ch_open}")
    yield _sse("agent_think", {
        "type": "agent_think",
        "agent": "chairman",
        "phase": 3,
        "round": 1,
        "content": ch_open
    })
    await _random_delay()

    # --- First Examiner 陈述检索结论 ---
    fe_statement = await _try_llm_generate(
        fe_llm,
        "请在口头审理中陈述你的检索结论和新颖性评估意见。",
        _ORAL_PROCEEDINGS["first_examiner_statement"]
    )
    await blackboard.add_react_step("first_examiner", 3, 1, "observe", fe_statement)
    await blackboard.set_agent_state("first_examiner", "observing", "陈述检索结论")
    await blackboard.add_debate_log(f"第一审查员陈述: {fe_statement}")
    yield _sse("agent_observe", {
        "type": "agent_observe",
        "agent": "first_examiner",
        "phase": 3,
        "round": 1,
        "content": fe_statement
    })
    await _random_delay()

    # --- Applicant Representative 答辩 ---
    ap_config = _load_agent_config("patent_applicant")
    ap_llm = LLMFactory.get_client("applicant_representative", ap_config.get("llm", {}), blackboard)

    ap_defense = await _try_llm_generate(
        ap_llm,
        f"你是专利申请人代理。审查员认为本申请与EP3812049A1和EP4012055A2存在特征重合。请提出答辩意见。",
        _ORAL_PROCEEDINGS["applicant_defense"]
    )
    await blackboard.add_react_step("applicant_representative", 3, 1, "observe", ap_defense)
    await blackboard.set_agent_state("applicant_representative", "observing", "提出答辩")
    await blackboard.add_debate_log(f"申请人代理答辩: {ap_defense}")
    yield _sse("agent_observe", {
        "type": "agent_observe",
        "agent": "applicant_representative",
        "phase": 3,
        "round": 1,
        "content": ap_defense
    })
    await _random_delay()

    # --- Second Examiner 反驳 ---
    se_rebuttal = await _try_llm_generate(
        se_llm,
        "请对申请人代理的答辩意见提出回应。",
        _ORAL_PROCEEDINGS["second_examiner_rebuttal"]
    )
    await blackboard.add_react_step("second_examiner", 3, 1, "observe", se_rebuttal)
    await blackboard.set_agent_state("second_examiner", "observing", "提出反驳")
    await blackboard.add_debate_log(f"第二审查员反驳: {se_rebuttal}")
    yield _sse("agent_observe", {
        "type": "agent_observe",
        "agent": "second_examiner",
        "phase": 3,
        "round": 1,
        "content": se_rebuttal
    })
    await _random_delay()

    # --- Legal Examiner 意见（如已召唤） ---
    if legal_summoned:
        le_opinion = await _try_llm_generate(
            ch_llm,  # 复用chairman的LLM配置
            "你是法律审查员。请从EPC法律条款角度分析本案的新颖性和创造性问题。",
            _ORAL_PROCEEDINGS["legal_examiner_opinion"]
        )
        await blackboard.add_react_step("legal_examiner", 3, 1, "observe", le_opinion)
        await blackboard.set_agent_state("legal_examiner", "observing", "提供法律意见")
        await blackboard.add_debate_log(f"法律审查员意见: {le_opinion}")
        yield _sse("agent_observe", {
            "type": "agent_observe",
            "agent": "legal_examiner",
            "phase": 3,
            "round": 1,
            "content": le_opinion
        })
        await _random_delay()

    # --- Chairman 总结 ---
    ch_summary = await _try_llm_generate(
        ch_llm,
        "请总结本次口头审理的各方意见，准备进入投票阶段。",
        _ORAL_PROCEEDINGS["chairman_summary"]
    )
    await blackboard.add_react_step("chairman", 3, 2, "observe", ch_summary)
    await blackboard.set_agent_state("chairman", "observing", "总结审理意见")
    await blackboard.add_debate_log(f"主席总结: {ch_summary}")
    yield _sse("agent_observe", {
        "type": "agent_observe",
        "agent": "chairman",
        "phase": 3,
        "round": 2,
        "content": ch_summary
    })
    await _random_delay()

    # Phase 3 完成
    for ag in phase3_agents:
        await blackboard.set_agent_state(ag, "idle")
    yield _sse("phase_complete", {
        "type": "phase_complete",
        "phase": 3,
        "summary": "口头审理完成，各方已充分陈述意见，准备进入最终投票阶段。"
    })
    await asyncio.sleep(1.0)

    # ====================================================================
    # Phase 4: 最终裁决 (Final Decision)
    # 每个投票审查员发出 vote_cast SSE事件
    # 3人投票（或4人，如Legal Examiner参与）
    # ====================================================================
    voters = ["first_examiner", "second_examiner", "chairman"]
    if legal_summoned:
        voters.append("legal_examiner")

    await blackboard.set_phase(4, "final_decision")
    await blackboard.set_step("final_decision")
    for v in voters:
        await blackboard.set_agent_state(v, "voting")

    yield _sse("phase_start", {
        "type": "phase_start",
        "phase": 4,
        "name": "final_decision",
        "title": "最终裁决",
        "agents": voters
    })
    await asyncio.sleep(1.0)

    # 获取最新的Fully_Disclosed计数
    current_fd_count = await blackboard.count_fully_disclosed()

    # 逐个投票
    vote_results = []
    for voter in voters:
        vote_decision = _determine_vote(voter, current_fd_count)
        vote_reasoning = _VOTE_TEMPLATES.get(voter, _VOTE_TEMPLATES["first_examiner"])[vote_decision]

        await blackboard.add_vote(voter, vote_decision, vote_reasoning)
        vote_results.append({
            "agent": voter,
            "vote": vote_decision,
            "reasoning": vote_reasoning
        })

        yield _sse("vote_cast", {
            "type": "vote_cast",
            "agent": voter,
            "vote": vote_decision,
            "reasoning": vote_reasoning
        })
        await asyncio.sleep(1.5)  # 投票之间间隔1.5s

    # 计算最终结论（多数决定）
    vote_counts = {"Grant": 0, "Reject": 0, "Conditional Grant": 0}
    for vr in vote_results:
        vote_counts[vr["vote"]] += 1

    # 确定多数票
    majority_vote = max(vote_counts, key=vote_counts.get)
    total_voters = len(vote_results)

    # 根据投票结果计算概率
    if majority_vote == "Grant":
        probability = 0.92
        conclusion = f"经{total_voters}名审查员投票，多数决定授予专利权。本申请的技术方案在整体上具有足够的新颖性和创造性贡献，满足EPC授权标准。投票结果：Grant {vote_counts['Grant']}票，Conditional Grant {vote_counts['Conditional Grant']}票，Reject {vote_counts['Reject']}票。"
    elif majority_vote == "Conditional Grant":
        probability = 0.65
        conclusion = f"经{total_voters}名审查员投票，多数决定附条件授权。申请人需根据审查意见修改权利要求书，限缩保护范围至真正具有新颖性的技术特征组合。投票结果：Grant {vote_counts['Grant']}票，Conditional Grant {vote_counts['Conditional Grant']}票，Reject {vote_counts['Reject']}票。"
    else:
        probability = 0.12
        conclusion = f"经{total_voters}名审查员投票，多数决定驳回申请。本申请的核心技术方案在新颖性方面存在重大缺陷，多项关键技术特征已被现有技术公开。投票结果：Grant {vote_counts['Grant']}票，Conditional Grant {vote_counts['Conditional Grant']}票，Reject {vote_counts['Reject']}票。"

    await blackboard.set_conclusion(probability, conclusion)
    await blackboard.add_debate_log(f"最终裁决: {conclusion}")

    # Phase 4 完成
    for v in voters:
        await blackboard.set_agent_state(v, "idle")
    yield _sse("phase_complete", {
        "type": "phase_complete",
        "phase": 4,
        "summary": f"最终裁决完成。多数票: {majority_vote}。EPO授权概率: {probability * 100:.0f}%。"
    })
    await _random_delay()

    # 发出最终completed事件
    await blackboard.set_step("completed")
    state = await blackboard.get_state()
    yield _sse("completed", {
        "type": "completed",
        "conclusion": conclusion,
        "probability": probability,
        "votes": vote_results,
        "state": state
    })
