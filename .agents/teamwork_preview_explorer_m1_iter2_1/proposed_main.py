import asyncio
import json
import uuid
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# MOCK IMPLEMENTATION FOR WORKFLOW DEMONSTRATION
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, # FIXED: cannot use True with origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

resume_events: Dict[str, asyncio.Event] = {}

class ResumeRequest(BaseModel):
    action: str
    details: str

@app.get("/api/v1/analyze/stream")
async def analyze_stream():
    async def event_generator():
        # Yield node_start
        yield f"event: node_start\ndata: {json.dumps({'message': 'Starting analysis'})}\n\n"
        
        # Generate ID and wait for resume
        interrupt_id = str(uuid.uuid4())
        event = asyncio.Event()
        resume_events[interrupt_id] = event
        
        yield f"event: hitl_interrupt\ndata: {json.dumps({'id': interrupt_id, 'message': 'Waiting for user input'})}\n\n"
        
        try:
            # FIXED: Added timeout to prevent resource exhaustion
            await asyncio.wait_for(event.wait(), timeout=300)
        except asyncio.TimeoutError:
            yield f"event: error\ndata: {json.dumps({'message': 'Timeout waiting for user input'})}\n\n"
            return
        finally:
            # FIXED: Memory leak cleanup if generator is cancelled
            if interrupt_id in resume_events:
                del resume_events[interrupt_id]
        
        # Once resumed
        yield f"event: completed\ndata: {json.dumps({'message': 'Analysis complete'})}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/v1/evaluation/{id}/resume")
async def resume_evaluation(id: str, req: ResumeRequest):
    if id in resume_events:
        resume_events[id].set()
        return {"status": "resumed"}
    return {"status": "error", "message": "ID not found"}
