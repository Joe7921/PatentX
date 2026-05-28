# Agent 协同工作流防碰撞隔离协议 (Branching & Verification SOP)

> **生效级别**：全局最高级别 (P0)
> **目的**：杜绝多 Agent 协同工作或历史版本覆盖导致的代码丢失、状态污染与依赖组件删除。

## 1. 原生沙盒隔离调用规范
任何负责下发多智能体任务（例如 /teamwork-preview）的统筹 Agent，在调用 `invoke_subagent` 工具拉起子智能体去执行“可能破坏全局组件”、“大规模UI重构”、“后台测试分析”等任务时，**必须强制**在调用参数中指定：
```json
{
  "Workspace": "branch"
}
```
**严禁**让执行大规模结构变更的 Subagent 在默认的 `inherit` (共享物理文件) 模式下工作。通过 `Workspace: 'branch'`，Antigravity 底层引擎会自动为其分支独立的物理沙盒，确保即使子 Agent 暴走或基于旧快照操作，也不会污染真实的 `main` 主干代码。

## 2. 状态同步与写时复制 (State Sync)
对于必须在主干 (inherit 模式) 工作以保持最新交互进度的 Agent：
- 在调用 `replace_file_content` 或 `write_to_file` 之前，如果涉及核心文件，必须先用 `view_file` 或 `grep_search` 确认文件的当前真实内容（例如确认 `UploadHub.tsx` 是否已经不是自己认知中的旧版本）。
- 盲目覆盖操作将被视为严重违规。

## 3. 防误删结界 (Protected Files Registry)
对于全局核心骨架，系统维护了一个受保护的名单。
- 路径：`.agent/protected_files.json`
- **规则**：除非用户显式下达“请废弃/重构 Sidebar”这类具有明确指向性的指令，否则任何常规任务 Agent 绝不能试图删除受保护名单中的文件。如果认为某受保护组件不再需要，必须先在 `implementation_plan.md` 中向人类发起 `request_feedback` 询问。

## 4. 构建与验证 (Build Verification)
在独立沙盒 (`Workspace: 'branch'`) 内工作的 Subagent 完成任务时：
1. 必须在其沙盒内自行跑通本地构建。
2. 将核心 Diff 和执行结果发送回统筹 Agent 的信箱（通过 `send_message`）。
3. 统筹 Agent 负责将成果提炼展示给用户，由用户确认“合并”后，沙盒代码才允许合入主项目。
