## 2026-05-23T13:17:12Z

请执行 PatentX UI/UX 全景重塑里程碑 M1：依赖审计与后端 SSE 适配。

具体任务：
1. **修改后端批注单元格定位逻辑**：在 `tools/patent_tools.py` 中引入国内特征唯一ID（可为特征在列表中的索引 df_id，如 `DF_0`, `DF_1` 等，或由你设计的唯一标示符），将批注定位键 `annotation_key` 从原本的 `f"{prior_art_id}_{prior_art_feature['id']}"` 重构为三维联合坐标键 `f"{domestic_feature_id}_{prior_art_id}_{prior_art_feature['id']}"`。需要确保调用该生成对齐矩阵函数的其他地方也同步适配，包括传入正确的 domestic_feature_id。
2. **修改 Resume 批注端点**：修改 `server/main.py` 的 `/api/v1/evaluation/{id}/resume` POST 端点，使其能够正确接收和反序列化前端传来的包含三维联合键的批注字典，并将这些批注写入 Blackboard 的 `expert_annotations` 中。
3. **实现第二轮辩论与决策注入**：在专家批注 Resume 后，如果在 Blackboard 中存在对某一单元格的专家批注（即 `status` 被修正为 `[专家修正]` 或者是特定的批注状态），构造 Layer L2 Agent（申请人代理和审查员）的提示词时，将该专家的批注理由（`details`） and 重新评估的数据作为 Context 传入，以便在第二轮辩论中重新计算授权概率，并通过 SSE 输出新的辩论内容。
4. **前端依赖安装 (Zustand)**：在 `frontend` 目录下安装 `zustand` 依赖（可执行终端命令如 `npm install zustand` 或 `yarn add zustand`），用于后续的全局状态机与 SSE 连接容灾实现。安装完成后，运行 `npm run build` 进行验证，确保前端构建成功，无任何编译或类型错误。
5. **后端功能测试与构建验证**：修改完成后，请运行后端测试（例如运行 `python verify_backend.py` 或者是测试指令），并记录测试命令和运行结果，确保后端没有报错，接口契约仍然有效。
6. 将你修改的文件、具体设计、前端构建与后端测试验证命令 and 结果，详细写入你的工作目录（`.agents/worker_m1/`）下的 `handoff.md` 中。
7. **语言规则**：你必须始终使用【简体中文】编写代码注释、提交说明 and handoff。
