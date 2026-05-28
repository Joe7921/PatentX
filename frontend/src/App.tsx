import React from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import Sidebar from './components/Sidebar';
import LandingPage from './components/LandingPage';
import DynamicTopoGraph from './components/DynamicTopoGraph';
import DiagnosticDashboard from './components/DiagnosticDashboard';
import DocumentPreview from './components/DocumentPreview';
import AuroraBackground from './components/AuroraBackground';
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
      <Sidebar />
      
      <div className="min-h-screen relative ml-[56px] text-slate-800 font-inter">
        
        {/* 容灾/错误状态轻提示 */}
        {error && step !== 'UPLOAD' && (
          <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 px-4 py-2.5 bg-red-50 border border-red-200 text-red-700 text-xs rounded-card flex items-center gap-2 shadow-gemini-md">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
            <span>{error}</span>
          </div>
        )}

        <AnimatePresence mode="wait">
          {/* UPLOAD 状态：极简沉浸式登场 */}
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

          {/* THINKING & PAUSED 状态：双侧沉浸式工作台 */}
          {(step === 'THINKING' || step === 'PAUSED') && (
            <motion.div
              key={step}
              layoutId="inputHub"
              initial={{ borderRadius: 28 }}
              animate={{ borderRadius: 24 }}
              transition={{ duration: 0.5, ease: [0.32, 0.72, 0, 1] }}
              className="w-full max-w-7xl mx-auto h-[calc(100vh-32px)] flex gap-5 items-stretch p-4 mt-8 relative bg-white/20 backdrop-blur-3xl border border-white/40 shadow-[0_8px_32px_rgba(0,0,0,0.08)]"
            >
              {/* 吸附极光背光阴影效果（现采用真实 Canvas 引擎渲染） */}
              <div className="absolute inset-[-100px] z-0 pointer-events-none opacity-50">
                <AuroraBackground isHovered={true} />
              </div>
              
              {/* 左侧栏：存放 DynamicTopoGraph */}
              <motion.div layoutId="timeline-pane" className="w-[40%] bg-white/90 backdrop-blur-md border border-gemini-outline/50 rounded-card p-5 relative overflow-y-auto overflow-x-hidden custom-scrollbar shadow-gemini-md z-10">
                <DynamicTopoGraph />
              </motion.div>

              {/* 右侧栏：存放 DocumentPreview */}
              <motion.div layoutId="preview-pane" className="w-[60%] bg-white/90 backdrop-blur-md border border-gemini-outline/50 rounded-card p-5 relative overflow-y-auto overflow-x-hidden flex flex-col custom-scrollbar shadow-gemini-md z-10">
                <DocumentPreview />
              </motion.div>
            </motion.div>
          )}

          {/* DASHBOARD 状态 */}
          {step === 'DASHBOARD' && (
            <motion.div
              key="DASHBOARD"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.25, ease: "easeInOut" }}
              className="w-full max-w-5xl mx-auto p-6"
            >
              <div className="bg-white border border-gemini-outline rounded-card p-8 shadow-gemini-xs">
                <DiagnosticDashboard />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  );
}

export default App;
