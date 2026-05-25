import sys
import os
import asyncio
import json
import uuid
import yaml
import importlib
from typing import Dict, List, Any, Union

# 将项目根目录和 server 目录均加入 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from blackboard import Blackboard
from tools.patent_tools import search_patent_db, generate_feature_alignment_matrix
from llm_factory import LLMFactory
from agentic_engine import run_agentic_workflow

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

resume_events: Dict[str, asyncio.Event] = {}
blackboards: Dict[str, Blackboard] = {}
api_adapters: Dict[str, Any] = {}

class ResumeRequest(BaseModel):
    action: str  # "Approve" or "Revise"
    details: Union[str, Dict[str, Any]]

def load_class(class_path: str):
    """
    通过类路径动态加载 Python 类
    """
    module_name, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)

def init_api_pool():
    """
    加载 api_pool.yaml 配置文件并初始化所有数据源 API 适配器
    """
    global api_adapters
    server_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(server_dir, "api_pool.yaml")
    if not os.path.exists(config_path):
        print("Warning: api_pool.yaml not found. Adapters will fallback to mock.")
        return
        
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    for name, adapter_cfg in config.get("adapters", {}).items():
        class_path = adapter_cfg["class_path"]
        try:
            cls = load_class(class_path)
            api_adapters[name] = cls(adapter_cfg)
            print(f"Loaded API adapter '{name}' from {class_path}")
        except Exception as e:
            print(f"Failed to load API adapter '{name}' ({class_path}): {e}")

def load_agent_config(agent_name: str) -> Dict[str, Any]:
    """
    加载 app/agents/_custom/ 中的 Agent YAML 配置
    """
    server_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(server_dir)
    config_path = os.path.join(project_dir, "app", "agents", "_custom", f"{agent_name}.yaml")
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# 初始化 API 池
init_api_pool()

@app.get("/api/v1/analyze/stream")
async def analyze_stream(claim: str = Query(default="一种嵌套多Agent协作与流式状态同步挂起的智能专利检索及评估系统，且具有安全验证恢复机制")):
    """
    流式分析端点:
    使用4阶段EPO审查工作流Agentic引擎，通过SSE推送每个ReAct步骤。
    阶段: 文档分析与检索 → 内部审查会议 → 口头审理 → 最终裁决
    """
    eval_id = str(uuid.uuid4())
    event = asyncio.Event()
    resume_events[eval_id] = event

    # 实例化当前任务的 Blackboard
    blackboard = Blackboard()
    blackboards[eval_id] = blackboard

    async def event_generator():
        try:
            # 委托给4阶段Agentic引擎生成SSE事件
            async for sse_event in run_agentic_workflow(
                blackboard=blackboard,
                claim=claim,
                eval_id=eval_id,
                resume_event=event
            ):
                yield sse_event
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'type': 'error', 'message': f'Internal Server Error: {str(e)}'}, ensure_ascii=False)}\n\n"
        finally:
            if eval_id in resume_events:
                del resume_events[eval_id]
            asyncio.create_task(cleanup_blackboard(eval_id, 300))

    return StreamingResponse(event_generator(), media_type="text/event-stream")

async def cleanup_blackboard(eval_id: str, delay: int):
    await asyncio.sleep(delay)
    if eval_id in blackboards:
        del blackboards[eval_id]

@app.post("/api/v1/evaluation/{id}/resume")
async def resume_evaluation(id: str, req: ResumeRequest):
    if id not in resume_events:
        raise HTTPException(status_code=404, detail="Evaluation task not found or already completed")
        
    blackboard = blackboards.get(id)
    if not blackboard:
        raise HTTPException(status_code=404, detail="Blackboard not found")

    try:
        if isinstance(req.details, str):
            try:
                annotations = json.loads(req.details)
            except json.JSONDecodeError:
                annotations = req.details
        else:
            annotations = req.details

        if isinstance(annotations, dict):
            for k, v in annotations.items():
                await blackboard.add_expert_annotation(k, v)
            await blackboard.add_debate_log(f"人类专家介入：提交了 {len(annotations)} 项特征对比状态的修正意见。决策类型：{req.action}")
        else:
            await blackboard.add_expert_annotation("global_comment", str(req.details))
            await blackboard.add_debate_log(f"人类专家介入：提交了全局批注。决策类型：{req.action}")
    except Exception as e:
        await blackboard.add_expert_annotation("global_comment", str(req.details))
        await blackboard.add_debate_log(f"人类专家介入：提交了全局批注且发生解析异常：{str(e)}。决策类型：{req.action}")

    resume_events[id].set()
    return {"status": "resumed"}

@app.get("/api/v1/evaluation/{id}/blackboard")
async def get_evaluation_blackboard(id: str):
    blackboard = blackboards.get(id)
    if not blackboard:
        raise HTTPException(status_code=404, detail="Evaluation task blackboard not found")
    return await blackboard.get_state()
