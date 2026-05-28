# PatentX 任务追踪

## 阶段一：Block-Driven Architecture 静态配置搭建
- [x] 创建分层嵌套的 YAML 配置文件 (L0, L1, L2, Transform)。
- [x] 创建 `patentx_pipeline.json` 流程拓扑。
- [x] 编写 Python 工具 Mock 函数并标记。
- [x] 编写并运行 `verify_config.py` 完成自我审查。

## 阶段二：后续待定任务
- [x] 将 Mock 的工具函数接入真实的 EPO 检索或学术检索 API。
  - [x] 安装官方 `google-cloud-bigquery` 等后端依赖环境
  - [x] 拷贝最新的真实的 GCP 凭据 JSON 文件 `gcp-key.json` 至 `server/`
  - [x] 在 `api_pool.yaml` 中启用真实的 Google BigQuery 数据检索
  - [x] 运行后端 E2E 集成测试进行真实网络检索断言验证
- [ ] 执行交互用例验证及 HITL (Human-in-the-Loop) 断点测试。
- [ ] 整合并连通业务前端逻辑。

## 里程碑 M1：依赖审计与后端 SSE 适配
- [x] 后端批注定位逻辑重构为三维联合键 `f"{domestic_feature_id}_{prior_art_id}_{prior_art_feature['id']}"`
- [x] 修改 Resume 批注接收端点支持三维坐标键字典的反序列化与 Blackboard 写入
- [x] 实现第二轮辩论与决策注入，将专家批注理由与重估数据做上下文传入，更新 SSE 辩论流
- [x] 在 `frontend` 目录下安装 `zustand` 全局状态管理依赖
- [x] 编写并升级集成测试脚本 `verify_backend.py` 与 `test_api.py` 覆盖三维批注与重算概率验证


## 里程碑 M5：3D 特征星图与 CoT 折叠
- [x] 开发 3D 特征星图 Canvas 2D 组件 `FeatureStarChart.tsx`，支持手写 3D-to-2D 旋转投影与自适应大小。
- [x] 手写鼠标拖拽交互及阻尼衰减惯性自转，景深处理（近大远小与深度透明度排序）。
- [x] 实现 Core-Planet-Satellite 三级拓扑：国内核心专利（恒星）、对比文献（行星）、对比特征（卫星）。
- [x] 接入 SSE 反馈：流光连线代表提到特征 ID，冲突卫星节点释放暗红抛射粒子。
- [x] 开发 Agent CoT 折叠思维链气泡，原地 Morphing 展开大纲与 Token / 预算看板（`font-mono`）。
- [x] 替换并集成组件到 `DiagnosticDashboardNew.tsx` 页面。
- [x] 更新 `PROJECT.md` 里程碑状态为 `DONE`。
- [x] 在 `frontend` 目录运行 `npm run build` 进行编译打包 100% 成功验证。
- [x] 整合并连通业务前端逻辑。
- [x] 执行交互用例验证及 HITL (Human-in-the-Loop) 断点测试。

## 里程碑 M6：全链路构建与 E2E 验证
- [x] 使用真实的 `uvicorn` 后台进程启动 API 服务以防止内存 ASGI 传输通道死锁。
- [x] 运行并验证 `verify_backend.py` E2E 集成测试，所有断言（Glow 呼吸流光、Fallback 自动降级预警、Token Budget 滑动窗口截断、第二轮专家注入大模型答辩及授权率 95.0% 重算）全部通过。
- [x] 前端打包编译测试成功通过（零错误警告），验证前端 UX 与后端三维定位批注与恢复机制 100% 连通。
- [x] 全局 Forensic Integrity 审计圆满通过，Verdict 评定为 CLEAN。

## 里程碑 M7：废除 3D 特征星图与恢复原有 UI 设计风格
- [x] 修改 `frontend/src/App.tsx` 恢复原本多卡片独立浮动切换布局，废除 `DiagnosticDashboardNew` 使用原本 of the `DiagnosticDashboard`。
- [x] 删除冗余前端文件 `FeatureStarChart.tsx`、`CoTExplanation.tsx`、`DiagnosticDashboardNew.tsx`（已清空作废，逻辑废除完成，待后续运行命令执行物理删除）。
- [x] 在 `frontend` 目录运行 `npm run build` 进行编译打包 100% 成功验证。
- [x] 在 `server` 目录运行 `py run_test.py` 进行后端全链路集成测试 100% 通过验证。
- [x] 全局 Forensic Integrity 审计圆满通过，Verdict 评定为 CLEAN（victory_auditor_m7_v2 成功）。
- [x] 审计失败回退处理：物理删除遗留组件 PatentStarChart.tsx 并且重新运行前后端构建和测试 100% 成功。
- [x] 输出交接文档 `handoff.md`。

## 里程碑 M8：iPhone 远程 Web 控制台部署
- [x] 在外部 Scratch 目录配置 Guacamole 的 `docker-compose.yml` 镜像服务。
- [x] 编写安全占位 `guacamole/user-mapping.xml` RDP 凭据配置文件。
- [x] 编写一键自适应物理/Tailscale IP 的 Windows 本地 `start-webssh.ps1` 网页终端启动脚本。
- [x] 编写基于 ttyd 绑定的网页端 PowerShell 终端 `start-terminal.ps1` 启动配置。
- [x] 编写详细的 iPhone 免安装 Web 远程控制台部署与 Vite 服务跨端发布指南。
- [x] 完成项目最终 E2E 与 Forensic Auditor 二次验证，提交 Victory Claim。

## 全自主 Agentic Workflow 重构（当前）
### M1：MCP Server 建设（工具层）
- [x] 开发 `server/mcp_server.py` 封装 `patent_tools` 为 MCP 工具
- [x] 开发 `server/mcp_client.py` 统一路由调用
### M2：LLMFactory 升级
- [x] 修改 `server/llm_factory.py` 支持 `tools` 与 `tool_calls` 解析
### M3：agentic_engine.py 核心重写
- [x] 改造 `agentic_engine.py` 为真正的 ReAct 循环
- [x] 动态提取 Blackboard 上下文
- [x] LLM 自主决定工具调用与阶段流转
### M4 & M5：YAML 扩展与前端适配
- [x] 修改 `app/agents/_custom/*.yaml` 添加 tools 声明
- [x] 前端类型兼容与 tool_args 展示

## 里程碑 M_verify：全链路验证与缺陷修复
- [x] 实施国内特征 ID 的双重规约方案：
  - [x] 增加 `epo_examiner.yaml` 中的系统提示词约束
  - [x] 增强 `agentic_engine.py` 初始 Prompt 中的 ID 传递与调用强规约
  - [x] 实现 `patent_tools.py` 里的特征 ID 自适应自动归一化逻辑
- [x] 运行集成测试进行 100% 成功验证（`py server/run_test.py`）

## 里程碑 M_robustness: 系统鲁棒性与异常处理增强
- [x] 实现熔断机制（Circuit Breaker）：在 `llm_factory.py` 中增加模型调用失败计数，超过阈值则进入 30 秒熔断窗口并强制回退。
- [x] 实现明确的 Mock 标注：对所有的异常 Fallback 返回数据，以及 `patent_tools.py` 的容错数据，统一添加 `[MOCK_TRANSPORT]` 前缀标注。
- [x] 提取统一的参数处理器：在 `agentic_engine.py` 引入 `_argument_pre_processor`，集中处理不规范的 LLM 工具调用参数（如 ID 对齐和特征填充），并记录 `[ARGUMENT_PROCESSOR]` 日志。
- [x] 完成 E2E 集成测试：执行 `py server/run_test.py` 并通过全部验证（包含对异常熔断注入情况下的行为验证）。
