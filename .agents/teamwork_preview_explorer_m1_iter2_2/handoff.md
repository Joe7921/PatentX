# Fix Strategy for Iteration 1

## Observation
The Auditor correctly identified multiple issues:
1. **Frontend Facade**: The React frontend is entirely static, with hardcoded components (`DiagnosticDashboard`, `UploadHub`, `ThinkingIndicator`, `AgenticPauseCard`) and zero real state management (`useState`, `useEffect`) or SSE event consumption (`EventSource`).
2. **Backend Memory Leak**: `resume_events[interrupt_id]` in `server/main.py` is not cleaned up if the connection drops or times out.
3. **Backend Resource Exhaustion**: The `await event.wait()` call waits indefinitely.
4. **Backend CORS Crash**: `allow_origins=["*"]` combined with `allow_credentials=True` crashes the FastAPI application on startup.
5. **Missing Comments**: The mock nature of the backend SSE was not explicitly commented in `server/main.py`.

## Logic Chain
1. To address the backend issues, `server/main.py` must be updated:
   - Change `allow_origins` to explicitly list frontend local URLs (`["http://localhost:5173", "http://127.0.0.1:5173"]`) to fix the CORS crash.
   - Add explicit mock documentation to `analyze_stream`.
   - Wrap the `await event.wait()` in an `asyncio.wait_for` with a timeout (e.g., 600 seconds) and handle `asyncio.TimeoutError` and `asyncio.CancelledError`.
   - Use a `finally` block to ensure the `interrupt_id` is popped from `resume_events` under all conditions, fixing the memory leak.
2. To address the frontend facade issue, genuine interaction must be implemented:
   - `DiagnosticDashboard.tsx` needs to manage the overall app state (`IDLE`, `STREAMING`, `PAUSED`, `COMPLETED`, `ERROR`) and hold the `EventSource` connection to `http://localhost:8000/api/v1/analyze/stream`.
   - Components like `UploadHub` must trigger the stream instead of just being visual.
   - `AgenticPauseCard` must trigger a POST request to `/api/v1/evaluation/{id}/resume` to actually resume the background process.

## Caveats
- Since this is a Teamwork explorer run with read-only restriction, I did not directly modify the source tree under `d:\Antigravity projects\PatentX`.
- Instead, I have placed proposed replacement files within my agent directory. The next implementer can copy or apply these.

## Conclusion
The application requires direct replacement of `server/main.py` and the frontend components to switch from a static facade to a genuinely connected state-machine. Proposed files have been generated:
- `proposed_main.py`
- `proposed_DiagnosticDashboard.tsx`
- `proposed_UploadHub.tsx`
- `proposed_AgenticPauseCard.tsx`

## Verification Method
1. Copy the proposed frontend files into `d:\Antigravity projects\PatentX\frontend\src\components\`.
2. Copy `proposed_main.py` to `d:\Antigravity projects\PatentX\server\main.py`.
3. Start the backend (`uvicorn main:app --reload`) and ensure it doesn't crash on startup (verifying the CORS fix).
4. Start the frontend (`npm run dev`) and click "Browse Files / Start MOCK Analysis".
5. Verify the state changes to `STREAMING`, then pauses and shows the `AgenticPauseCard`. Click "Resume" and verify it finishes as `COMPLETED`.
6. Run `pytest verify_backend.py` to ensure backend still passes tests.
