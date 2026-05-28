# 分析报告：还原 LandingPage 与首屏设计

## 问题边界与观察 (Observation)
1. **现状分析**：当前 `App.tsx` 中的 `UPLOAD` 状态直接渲染了被 `<motion.div className="glass-panel ...">` 包裹的 `UploadHub`。这导致原本的开屏 Slogan ("Tech Is All You Need")、SpaceX 风格 Logo 以及专属的交互式极光光晕丢失。
2. **Git 历史追踪**：通过查找 Git 历史记录发现，`LandingPage.tsx` 和 `TypewriterSlogan.tsx` 曾在 commit `b36acd0a...` 中被引入，同时该 commit 也修改了 `AuroraBackground.tsx` 以提供一个紧贴 `UploadHub` 的悬停交互光晕。
3. **组件冲突**：目前 `frontend/src/components/AuroraBackground.tsx` 是一个全局的背景组件，与 `LandingPage` 依赖的悬停光晕版本（`AuroraBackground.bak.tsx`）存在功能和设计上的分歧。

## 逻辑推演 (Logic Chain)
为了在不破坏当前全局背景的情况下完美还原首屏设计：
1. **提取丢失组件**：从 Git 历史中成功提取并恢复了 `LandingPage.bak.tsx`、`TypewriterSlogan.bak.tsx` 和被修改的 `AuroraBackground.bak.tsx`。
2. **隔离光晕组件**：将旧版的局部交互式 `AuroraBackground` 重命名为 `AuroraGlow.tsx`，以专门作为 `UploadHub` 的底部发光垫。这样可以保留全局背景 `<AuroraBackground />` 在 `App.tsx` 中的正常运作。
3. **复用逻辑**：`LandingPage` 本身已经正确地封装了 Logo、`TypewriterSlogan` 和 `UploadHub`，并将 `onUpload` 回调传递给了 `UploadHub`，这与 Zustand Store 的 `startAnalysis` 流程是完全兼容的。

## 结论与行动方案 (Conclusion & Proposed Changes)
我已经将复原并调整后的组件保存在了本工作区的 `proposed/` 目录下。接下来的实现应按照以下步骤进行：

1. **导入组件文件**：
   将本工作区 (`.agents/teamwork_preview_explorer_m1_2/proposed/`) 下的三个文件复制到项目源代码的 `frontend/src/components/` 目录中：
   - `LandingPage.tsx`
   - `TypewriterSlogan.tsx`
   - `AuroraGlow.tsx`

2. **修改 `App.tsx`**：
   移除当前包裹 `UploadHub` 的局部容器（包含 `.glass-panel` 等类名），将 `UPLOAD` 阶段直接指向全屏的 `LandingPage` 组件，并透传 `handleUpload`。

   **修改前的 `App.tsx` (节选)**：
   ```tsx
   {step === 'UPLOAD' && (
     <motion.div
       key="UPLOAD"
       initial={{ opacity: 0, y: 15, filter: 'blur(4px)' }}
       animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
       exit={{ opacity: 0, y: -15, filter: 'blur(4px)' }}
       transition={{ duration: 0.25, ease: "easeInOut" }}
       className="glass-panel w-full max-w-xl p-8 rounded-3xl relative overflow-hidden"
     >
       <UploadHub onUpload={handleUpload} />
     </motion.div>
   )}
   ```

   **修改后的 `App.tsx` (建议)**：
   ```tsx
   import LandingPage from './components/LandingPage';
   // ... 
   {step === 'UPLOAD' && (
     <motion.div
       key="UPLOAD"
       initial={{ opacity: 0, filter: 'blur(4px)' }}
       animate={{ opacity: 1, filter: 'blur(0px)' }}
       exit={{ opacity: 0, filter: 'blur(4px)' }}
       transition={{ duration: 0.25, ease: "easeInOut" }}
       className="absolute inset-0 z-10 w-full min-h-screen flex items-center justify-center"
     >
       <LandingPage onUpload={handleUpload} />
     </motion.div>
   )}
   ```
   *(注：由于 LandingPage 内置了 `y` 轴动画，外部包裹的 motion.div 不再需要纵向偏移量)*
