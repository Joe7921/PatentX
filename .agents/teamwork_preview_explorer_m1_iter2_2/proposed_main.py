import asyncio
import json
import uuid
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    # Fix CORS crash: allow_origins=["*"] with allow_credentials=True is forbidden
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

resume_events: Dict[str, asyncio.Event] = {}

class ResumeRequest(BaseModel):
    action: str
    details: str

@app.get("/api/v1/analyze/stream")
async def analyze_stream():
    """
    MOCK IMPLEMENTATION:
    This endpoint simulates a long-running analysis process that yields Server-Sent Events (SSE).
    """
    async def event_generator():
        # Yield node_start
        yield f"event: node_start\ndata: {json.dumps({'message': 'Starting analysis'})}\n\n"
        
        # MOCK: Generate ID and wait for resume
        interrupt_id = str(uuid.uuid4())
        event = asyncio.Event()
        resume_events[interrupt_id] = event
        
        yield f"event: hitl_interrupt\ndata: {json.dumps({'id': interrupt_id, 'message': 'Waiting for user input'})}\n\n"
        
        try:
            # Fix resource exhaustion: add timeout
            await asyncio.wait_for(event.wait(), timeout=600.0)  # 10 minutes timeout
            # Once resumed
            yield f"event: completed\ndata: {json.dumps({'message': 'Analysis complete'})}\n\n"
        except asyncio.TimeoutError:
            yield f"event: error\ndata: {json.dumps({'message': 'Timeout waiting for user input'})}\n\n"
        except asyncio.CancelledError:
            pass # Client disconnected
        finally:
            # Fix memory leak: ensure event is cleaned up
            if interrupt_id in resume_events:
                del resume_events[interrupt_id]
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/v1/evaluation/{id}/resume")
async def resume_evaluation(id: str, req: ResumeRequest):
    if id in resume_events:
        resume_events[id].set()
        return {"status": "resumed"}
    return {"status": "error", "message": "ID not found"}
