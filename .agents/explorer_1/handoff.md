# Handoff Report: Fix Strategy for Streaming Infinite Loop

## 1. Observation
- 在查阅了 Reviewer 1 Iter 2 的 handoff 报告，并亲自查看了 `d:\Antigravity projects\PatentX\server\main.py` 和 `d:\Antigravity projects\PatentX\frontend\src\components\DiagnosticDashboard.tsx` 文件后，发现了以下两点直接相关的现象：
  1. `DiagnosticDashboard.tsx` 中的 `EventSource` 监听器（`onmessage` 以及 `addEventListener('hitl_interrupt')`）在收到 `hitl_interrupt` 事件时，执行了 `eventSource?.close()`，直接关闭了 SSE 连接。
  2. `server/main.py` 中的 `/api/v1/evaluation/{id}/resume` 路由在未找到对应 `id` 时，仅返回 `{"status": "error", "message": "ID not found"}`，并未抛出 HTTP 异常，导致默认的响应状态码为 200 OK。

## 2. Logic Chain
1. **连接断开导致后端清理资源**：前端在收到 `hitl_interrupt` 事件后调用 `eventSource.close()`。此时底层的 HTTP 长连接断开，FastAPI 端的生成器会捕获到 `asyncio.CancelledError`，随即执行 `finally` 块中的 `del resume_events[interrupt_id]`，从内存中删除了该 ID 对应的事件对象。
2. **错误的恢复尝试**：用户在前端点击继续（Approve/Revise）时，前端发送 POST 请求到 `/api/v1/evaluation/{evalId}/resume`。
3. **状态码掩盖错误**：由于后端事件已被删除，此 ID 不在 `resume_events` 中。后端返回了表示错误信息的 JSON，但状态码却是 200。
4. **前端误判导致死循环**：前端执行 `if (response.ok)` 判断为 `true`，进而清空了 `evalId` 并将状态重置为 `STREAMING`。由于 `workflowState` 变成了 `STREAMING`，`useEffect` 重新触发并创建了新的 `EventSource` 连接，导致整个流程从头开始，而非从中断点继续，从而陷入无限循环。

## 3. Caveats
- 这是一个纯粹的前后端状态同步与连接管理问题，当前的分析基于代码的静态审查，并未实际运行调试。但在 `EventSource` 的规范和 FastAPI 的异步流机制下，该逻辑链是确凿无疑的。
- 考虑到这是一个 MOCK 接口，后续如果有真实的后台任务调度（如基于 Celery/Redis 等），任务的状态管理可能需要进一步与连接管理解耦。目前的修复策略针对的是当前的内存字典实现。

## 4. Conclusion
**修复策略方案（不执行具体代码修改）：**

1. **前端修改（DiagnosticDashboard.tsx）**：
   - 移除在 `hitl_interrupt` 事件处理逻辑中对 `eventSource?.close()` 的调用（包括 `onmessage` 和 `addEventListener` 处）。在等待人工介入（HITL）期间，必须保持 SSE 连接开启，以接收后续的事件。
   - 保留原有的在 `completed` 事件和 `onerror` 以及 `useEffect` 清理函数中关闭连接的逻辑。
   - 确保当接收到 `hitl_interrupt` 时只更改 `workflowState` 和记录 `evalId`。

2. **后端修改（server/main.py）**：
   - 修改 `/api/v1/evaluation/{id}/resume` 路由，在未找到对应 ID 时，使用 FastAPI 的 `HTTPException` 抛出 `404 Not Found` 错误，而不是返回 200 OK 加上错误 JSON。
   - 例如：`raise HTTPException(status_code=404, detail="ID not found")`。
   - 这样前端在调用 `fetch` 恢复时，`response.ok` 将为 `false`，从而触发前端的错误处理，防止意外重置状态。

## 5. Verification Method
1. **代码检查**：核查 `DiagnosticDashboard.tsx` 中 `hitl_interrupt` 相关的分支，确认没有 `eventSource?.close()`；核查 `server/main.py` 中的 resume 路由，确认包含了 404 的抛出。
2. **构建验证**：在前端目录运行 `npm run build` 或对应的验证命令确认语法正确。
3. **功能测试**：启动后端与前端，触发流程并等待进入 Pause 状态。此时后端不应出现 Cancelled 错误。点击恢复按钮后，前端应当进入完成状态，而不是重新开始 `Initializing...`。
