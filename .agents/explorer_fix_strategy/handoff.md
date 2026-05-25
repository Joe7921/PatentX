# Handoff Report: Infinite Loop Fix Strategy

## 1. Observation
- **Frontend (`DiagnosticDashboard.tsx`)**:
  - `eventSource?.close()` is explicitly called inside the `hitl_interrupt` handlers (lines 28, 53).
  - The EventSource is managed inside a `useEffect` that depends on `[workflowState]`. The cleanup function for this effect calls `eventSource.close()` (lines 73-77). When `workflowState` transitions from `STREAMING` to `PAUSED`, this cleanup function is triggered, closing the connection even if the explicit `.close()` calls were removed.
- **Backend (`server/main.py`)**:
  - The FastAPI generator catches `asyncio.CancelledError` (line 52) when the client disconnects, triggering the `finally` block which deletes the `interrupt_id` from `resume_events` (line 57).
  - The POST `/api/v1/evaluation/{id}/resume` endpoint returns `{"status": "error", "message": "ID not found"}` with an HTTP 200 status code when the ID is not in `resume_events` (line 66).

## 2. Logic Chain
1. When the backend yields the `hitl_interrupt` event, the frontend changes `workflowState` to `PAUSED` and explicitly closes the `EventSource`.
2. Even without the explicit close, the state change to `PAUSED` triggers the `useEffect` cleanup, which also closes the `EventSource`.
3. The disconnection causes the backend generator to be cancelled (`asyncio.CancelledError`), executing the `finally` block and deleting the pause ID from memory.
4. When the user attempts to resume, the frontend sends a POST request to `/resume`. The backend cannot find the ID (since it was deleted) and returns an error message but with a `200 OK` HTTP status.
5. The frontend's `if (response.ok)` check passes because of the 200 status code. It then sets `workflowState` to `STREAMING`.
6. The `useEffect` triggers again, creating a *new* `EventSource` connection to the stream, starting the process from the beginning instead of resuming the paused job, resulting in an infinite loop.

## 3. Caveats
- No code has been modified during this investigation phase, as instructed.

## 4. Conclusion
**VERDICT: Fix Strategy Ready**

To fully resolve the infinite loop, the following strategy should be implemented:

**Frontend Fix Strategy**:
1. Remove all `eventSource?.close()` calls from the `hitl_interrupt` event handlers in `DiagnosticDashboard.tsx`.
2. **Crucial**: Refactor the EventSource lifecycle management so it is not torn down when `workflowState` changes to `PAUSED`. One approach is to remove `workflowState` from the `useEffect` dependencies and manage the `EventSource` imperatively using a `useRef` (e.g., creating it on `handleStartStream` and closing it only on component unmount, error, or `COMPLETED` state).

**Backend Fix Strategy**:
1. In `server/main.py`, modify the `/api/v1/evaluation/{id}/resume` endpoint to raise an HTTP exception when the ID is not found, ensuring the frontend recognizes it as an error.
   ```python
   from fastapi import HTTPException
   
   @app.post("/api/v1/evaluation/{id}/resume")
   async def resume_evaluation(id: str, req: ResumeRequest):
       if id in resume_events:
           resume_events[id].set()
           return {"status": "resumed"}
       raise HTTPException(status_code=404, detail="ID not found")
   ```

## 5. Verification Method
1. Inspect `server/main.py` to ensure `HTTPException(status_code=404)` is raised for missing IDs.
2. Inspect `DiagnosticDashboard.tsx` to verify that `eventSource.close()` is no longer triggered upon entering the `PAUSED` state (either by explicit call or hook cleanup).
3. Run the application, trigger a pause, approve it, and verify that the stream properly resumes and finishes (`COMPLETED`) without starting over.
