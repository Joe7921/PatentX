# Milestone 1: Backend Mock - Exploration Report

**Summary**: The backend mock requires a FastAPI application exposing a Server-Sent Events (SSE) endpoint that pauses mid-stream for Human-in-the-Loop (HITL) intervention, and a concurrent endpoint to resume it. Testing this requires asynchronous HTTP streaming support.

## 1. Observation
- `SCOPE.md` specifies `server/main.py` and `verify_backend.py` as deliverables.
- `ORIGINAL_REQUEST.md` requires:
  - `GET /api/v1/analyze/stream`: Yields `node_start`, `hitl_interrupt` (with `{ "id": "<eval_id>" }`), and `completed`.
  - `POST /api/v1/evaluation/{id}/resume`: Takes `{"action": "Approve|Revise", "details": "..."}`, returns `{"status": "resumed"}`.
  - The stream must pause at `hitl_interrupt` and continue only after the `/resume` endpoint is called.
  - `verify_backend.py` must assert `hitl_interrupt` is correctly emitted.

## 2. Logic Chain
- To pause the `GET` stream and resume it from a separate `POST` request, the server needs shared state. An in-memory dictionary mapping `eval_id` to `asyncio.Event()` instances is the most lightweight, native solution for a mock.
- Standard FastAPI `StreamingResponse` can stream strings formatted as `event: <name>\ndata: <json>\n\n` to comply with the `text/event-stream` standard.
- The `verify_backend.py` script needs to read the stream without blocking the main thread, so it can fire the `/resume` POST request concurrently. Using `httpx.AsyncClient` with an ASGI transport (passing the FastAPI `app` directly) allows testing the async stream and the resume endpoint without running a separate Uvicorn server subprocess.

## 3. Caveats
- The `asyncio.Event` dictionary is in-memory and will be lost on server restart. This is acceptable (and preferred) for a mock backend.
- The mock will not handle stream disconnection cleanly if the client drops before resume, but for testing the happy path it is sufficient.

## 4. Conclusion
We recommend the following architecture for implementation:

**server/main.py**:
1. Global state: `resume_events: dict[str, asyncio.Event] = {}`.
2. `/api/v1/analyze/stream`: 
   - Generates a UUID for `eval_id`.
   - Stores `asyncio.Event` in `resume_events`.
   - Yields `node_start` and `hitl_interrupt` containing the `eval_id`.
   - `await resume_events[eval_id].wait()`.
   - Upon awakening, cleans up the dict and yields `completed`.
3. `/api/v1/evaluation/{id}/resume`:
   - Looks up `id` in `resume_events`.
   - Calls `.set()` on the event to unblock the stream, returns success.

**verify_backend.py**:
1. Uses `httpx.AsyncClient(app=app, base_url="http://testserver")`.
2. Calls the stream endpoint in a background task or loops over `response.aiter_lines()`.
3. Asserts the arrival of `hitl_interrupt` and extracts the ID.
4. Concurrently calls `/resume` with the extracted ID.
5. Asserts the arrival of the `completed` event.

## 5. Verification Method
After implementation, run `python server/verify_backend.py`. The output should demonstrate the full stream lifecycle, successfully extracting the ID, triggering the resume, and receiving the `completed` event without hanging.
