# Milestone 1: Backend Mock Investigation Report

## 1. Observation
- `SCOPE.md` and `ORIGINAL_REQUEST.md` define Milestone 1: a FastAPI backend mock and a `verify_backend.py` testing script.
- The backend must provide two endpoints:
  - `GET /api/v1/analyze/stream`: Yields `text/event-stream` SSE events (`node_start`, `hitl_interrupt`, `completed`).
  - `POST /api/v1/evaluation/{id}/resume`: Accepts `{"action": "...", "details": "..."}` to resume the stream.
- A `verify_backend.py` script needs to start the server (or use `TestClient`), call the stream, and assert that `hitl_interrupt` is correctly emitted.

## 2. Logic Chain
- **Server Implementation**: 
  - FastAPI's `StreamingResponse` can be used for the `GET` endpoint.
  - To simulate the Human-In-The-Loop (HITL) pause, the stream generator can emit `hitl_interrupt` (including an evaluation ID) and then `await asyncio.Event().wait()` to suspend execution.
  - The `POST` resume endpoint will look up the `asyncio.Event` by evaluation ID and call `.set()`, allowing the stream to continue and emit `completed`.
- **Testing (`verify_backend.py`)**: 
  - Because SSE streaming is a long-running concurrent request, a simple synchronous `TestClient` is hard to use for pausing/resuming. 
  - Using `httpx.AsyncClient` with `ASGITransport` allows asynchronous, concurrent testing of both endpoints without needing to spawn a separate process for Uvicorn. The script can start a background task to consume the SSE stream and another to call the resume endpoint when `hitl_interrupt` is detected.

## 3. Caveats
- This is a mock backend. The evaluation ID can be a hardcoded UUID or simple string (e.g., `mock-eval-123`) since there's no actual database.
- CORS must be configured on the FastAPI app to allow the future React frontend to connect locally.
- Dependencies (`fastapi`, `uvicorn`, `httpx`) will need to be specified in a `requirements.txt` file and installed.

## 4. Conclusion
The implementation should consist of three files:
1. `server/requirements.txt`:
   ```text
   fastapi
   uvicorn
   httpx
   ```
2. `server/main.py`:
   Define the FastAPI app, include `CORSMiddleware`, and implement the endpoints using a global dictionary mapping `eval_id` to `asyncio.Event` to handle the pause/resume logic.
3. `server/verify_backend.py`:
   Use `asyncio` and `httpx.AsyncClient(transport=httpx.ASGITransport(app=app))` to asynchronously test the stream. Assert the arrival of `node_start`, `hitl_interrupt`, then send the POST request, and assert the final `completed` event.

## 5. Verification Method
- Ensure the environment has the required dependencies.
- Run `python server/verify_backend.py`. It should execute the test, assert the events, and exit with code 0.
- Optionally, run `uvicorn server.main:app --reload` and test via `curl` to manually verify SSE stream and POST resume behavior.
