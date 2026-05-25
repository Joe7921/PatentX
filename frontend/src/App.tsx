import React from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import UploadHub from './components/UploadHub';
import AgenticTimeline from './components/AgenticTimeline';
import DiagnosticDashboard from './components/DiagnosticDashboard';
import { AuroraBackground } from './components/AuroraBackground';
import { useStore } from './store/useStore';

function App() {
  const { 
    step, 
    error,
    startAnalysis, 
  } = useStore();

  const handleUpload = (claimText: string) => {
    // 启动分析流，传入用户输入的 Claim，如果为空则传入默认专利特征陈述
    startAnalysis(claimText || "一种嵌套多Agent协作与流式状态同步挂起的智能专利检索及评估系统，且具有安全验证恢复机制");
  };

  return (
    <>
      <AuroraBackground />
      <div className="min-h-screen relative flex items-center justify-center p-6 text-slate-800 font-inter">
        
        {/* 容灾/错误状态轻提示 */}
        {error && step !== 'UPLOAD' && (
          <div className="fixed top-6 left-1/2 transform -translate-x-1/2 z-50 p-3 bg-rose-500/20 border border-rose-500/30 text-rose-300 text-xs rounded-xl flex items-center justify-between shadow-lg backdrop-blur-md">
            <span>{error}</span>
          </div>
        )}

        <AnimatePresence mode="wait">
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

          {/* THINKING状态：渲染AgenticTimeline替代原ThinkingIndicator */}
          {step === 'THINKING' && (
            <motion.div
              key="THINKING"
              initial={{ opacity: 0, y: 15, filter: 'blur(4px)' }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
              exit={{ opacity: 0, y: -15, filter: 'blur(4px)' }}
              transition={{ duration: 0.25, ease: "easeInOut" }}
              className="glass-panel w-full max-w-4xl p-8 rounded-3xl relative overflow-hidden max-h-[85vh] overflow-y-auto"
            >
              <AgenticTimeline />
            </motion.div>
          )}

          {/* PAUSED状态：渲染AgenticTimeline，HITL节点自动展开 */}
          {step === 'PAUSED' && (
            <motion.div
              key="PAUSED"
              initial={{ opacity: 0, y: 15, filter: 'blur(4px)' }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
              exit={{ opacity: 0, y: -15, filter: 'blur(4px)' }}
              transition={{ duration: 0.25, ease: "easeInOut" }}
              className="glass-panel w-full max-w-4xl p-8 rounded-3xl relative overflow-hidden max-h-[85vh] overflow-y-auto"
            >
              <AgenticTimeline />
            </motion.div>
          )}

          {step === 'DASHBOARD' && (
            <motion.div
              key="DASHBOARD"
              initial={{ opacity: 0, y: 15, filter: 'blur(4px)' }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
              exit={{ opacity: 0, y: -15, filter: 'blur(4px)' }}
              transition={{ duration: 0.25, ease: "easeInOut" }}
              className="glass-panel w-full max-w-5xl p-8 rounded-3xl relative overflow-hidden"
            >
              <DiagnosticDashboard />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  );
}

export default App;
