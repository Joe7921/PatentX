# 首页重构与状态集成分析报告

## 1. 现状观察与问题定位

在当前的 `main` 分支（基于 `8ef36a1`）中，`App.tsx` 的首页状态 (`step === 'UPLOAD'`) 被直接硬编码为渲染 `<UploadHub>`：
```tsx
{step === 'UPLOAD' && (
  <motion.div
    key="UPLOAD"
    // ...
    className="glass-panel w-full max-w-xl p-8 rounded-3xl relative overflow-hidden"
  >
    <UploadHub onUpload={handleUpload} />
  </motion.div>
)}
```
同时，背景组件 `<AuroraBackground />` 作为一个无状态的全局 Canvas 被放置在 `App.tsx` 的顶层。

通过检索 Git 历史，我们发现 `b36acd0a6a9a34f87f647b4057e335b07b8bbf02` 提交曾经包含了经过精心设计的首屏组件：
- **`LandingPage.tsx`**: 负责组合 Logo、打字机 Slogan、UploadHub，并将光晕背景（AuroraBackground）动态地收束在输入舱边缘。
- **`TypewriterSlogan.tsx`**: 提供 "Tech Is All You Need" 的打字机动画效果。
- **`AuroraBackground.tsx`**: 该组件在这个版本中被改造为默认导出（`export default`），接受 `isHovered` 参数，以便响应用户的悬停动作实现光晕动态扩散。

**结论**：由于分支切换或覆盖，丢失了 `b36acd0` 中的 UI 变更。导致目前首屏只剩下一个简陋的 `UploadHub` 组件。

## 2. 恢复与集成方案

为了重建精心设计的首屏，并确保 Zustand 状态流正确流转，需要进行以下四步修改：

### 第一步：从 Git 历史恢复丢失的组件
从 `b36acd0` 提交中恢复以下三个文件到 `frontend/src/components/`：
1. `LandingPage.tsx`
2. `TypewriterSlogan.tsx`
3. `AuroraBackground.tsx`（覆盖当前版本，以支持 `isHovered` 属性和局部渲染）

### 第二步：修改 `App.tsx` 中的组件引入
移除旧的 `AuroraBackground` 命名导入，添加 `LandingPage` 导入：
```tsx
// 移除: import { AuroraBackground } from './components/AuroraBackground';
import LandingPage from './components/LandingPage';
```

### 第三步：移除 `App.tsx` 顶层的全局背景
在 `App.tsx` 的返回值中，删除顶层的 `<AuroraBackground />`。因为恢复后的 `AuroraBackground` 已经被集成到了 `LandingPage`（首页）、以及可能存在的其他组件内部，作为局部背景光晕存在。

### 第四步：将 `UPLOAD` 状态挂载到 `LandingPage`
修改 `App.tsx` 中 `step === 'UPLOAD'` 的渲染逻辑：
```tsx
{step === 'UPLOAD' && (
  <motion.div
    key="UPLOAD"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    transition={{ duration: 0.4 }}
    className="min-h-screen flex flex-col items-center justify-center px-6"
  >
    <LandingPage onUpload={handleUpload} />
  </motion.div>
)}
```

## 3. 状态流验证（Zustand Store 链路）
- **数据流向**：`UploadHub` 内部的 `textarea` -> 点击提交 -> 触发 `UploadHub` 接收到的 `onUpload(text)`。
- **组件透传**：`LandingPage` 通过 `onUpload={onUpload}` 将外部传入的事件处理器直接透传给 `UploadHub`，不改变任何参数。
- **顶层处理**：`App.tsx` 中的 `<LandingPage onUpload={handleUpload} />` 接收到参数，调用 `startAnalysis(claimText)`，进而成功触发 Zustand 状态机向 `THINKING` 的状态流转。

这套方案不仅完美恢复了包含 Logo、打字机、动态悬停光晕的沉浸式首屏体验，同时也保证了业务数据和状态流转链路的完整性。
