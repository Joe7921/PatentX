# Handoff Report: Milestone 1 Backend Mock Strategy

## 1. Observation
- `SCOPE.md` specifies the need for a FastAPI mock backend.
- Endpoints required: `GET /api/v1/analyze/stream` (SSE stream) and `POST /api/v1/evaluation/{id}/resume`.
- The stream must pause and emit `hitl_interrupt` containing an `{ "id": "<eval_id>" }`.
- `verify_backend.py` must test the stream generation, intercept the `hitl_interrupt`, and call the resume endpoint to unblock it.
- `server/` directory is not yet created.

## 2. Logic Chain
- **State Management**: To simulate a pause in the backend while keeping the SSE connection alive, we can use `asyncio.Event()` stored in a global dictionary (`evaluation_states = {}`) keyed by `eval_id`.
- **Stream Generation**: The `GET /api/v1/analyze/stream` endpoint will:
  1. Generate a UUID `eval_id`.
  2. Create an `asyncio.Event` and store it.
  3. Yield initial events using `fastapi.responses.StreamingResponse` (formatted as SSE `event: ...\ndata: ...\n\n`).
  4. Yield `hitl_interrupt` with the `eval_id`.
  5. Wait asynchronously: `await event.wait()`.
  6. Yield completion events after the event is set.
- **Resume Handling**: `POST /api/v1/evaluation/{id}/resume` will find the `asyncio.Event` by `id` and call `.set()`, thus unblocking the stream.
- **Verification Script**: Standard synchronous `TestClient` can block when consuming streams containing `asyncio` pauses. We should use `httpx.AsyncClient(app=app, base_url="http://test")` in `verify_backend.py` to concurrently read the stream lines and dispatch the POST request without blocking.
- **CORS**: The backend needs `CORSMiddleware` configured to `allow_origins=["*"]` to ensure the upcoming frontend Vite app can connect.

## 3. Caveats
- Using a global in-memory dictionary for state is strictly for mock purposes and would not work in a multi-worker production environment.
- The verification script's SSE parsing logic will be basic (reading string lines) rather than using a full SSE parser, which is perfectly sufficient for testing a predictable mock backend.

## 4. Conclusion
The implementation of the Backend Mock should proceed with the following files:
1. `server/requirements.txt`: Include `fastapi`, `uvicorn`, `httpx`.
2. `server/main.py`: Implement the FastAPI app, the `evaluation_states` dictionary, CORS middleware, and the two endpoints using `StreamingResponse`.
3. `server/verify_backend.py`: Implement an `asyncio` script that uses `httpx.AsyncClient` to connect to the ASGI app directly, iterates over `response.aiter_lines()`, parses the `hitl_interrupt` ID, sends the POST `/resume` request in a background task, and asserts the stream reaches completion.

## 5. Verification Method
- **Implementation Validation**: The implementer will create the files and install dependencies.
- **Command**: Run `python server/verify_backend.py`.
- **Success Criteria**: The script exits with code `0`, and its output confirms that `hitl_interrupt` was intercepted, ID was parsed, resume endpoint returned 200, and the stream successfully reached `completed`.
