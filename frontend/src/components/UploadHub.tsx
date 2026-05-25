import React, { useState, useEffect } from 'react';
import { Upload, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface UploadHubProps {
  onUpload: (claimText: string) => void;
  disabled?: boolean;
}

export default function UploadHub({ onUpload, disabled = false }: UploadHubProps) {
  const fullText = "基于多 Agent 嵌套辩论的欧洲专利局 EPO 诊断与特征对齐评估系统";
  const [displayText, setDisplayText] = useState("");
  const [typingDone, setTypingDone] = useState(false);
  const [claimValue, setClaimValue] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  // 流光打字机效果
  useEffect(() => {
    let currentIndex = 0;
    const interval = setInterval(() => {
      if (currentIndex < fullText.length) {
        setDisplayText(fullText.slice(0, currentIndex + 1));
        currentIndex++;
      } else {
        clearInterval(interval);
        setTypingDone(true);
      }
    }, 45); // 约45毫秒显示一个字
    return () => clearInterval(interval);
  }, []);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          setClaimValue(event.target.result as string);
        }
      };
      if (file.type.startsWith('text/') || file.name.endsWith('.txt') || file.name.endsWith('.md')) {
        reader.readAsText(file);
      } else {
        setClaimValue(`分析文件：${file.name}\n大小：${(file.size / 1024).toFixed(1)} KB`);
      }
    }
  };

  const isCollapsed = claimValue.length > 0 || isDragging;

  const handleSubmit = () => {
    onUpload(claimValue.trim());
  };

  return (
    <div 
      className={`flex flex-col items-center justify-center py-6 text-center transition-all ${
        disabled ? 'opacity-50 pointer-events-none' : ''
      }`}
      onDragOver={handleDragOver}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* 上传/拖拽图标 */}
      <Upload className={`w-16 h-16 mb-4 transition-all duration-300 ${
        isDragging ? 'text-blue-400 scale-110 animate-pulse' : 'text-blue-400/80 animate-bounce'
      }`} />

      {/* 流光打字机标题 */}
      <h3 className="text-xl font-bold bg-gradient-to-r from-blue-400 via-indigo-300 to-cyan-400 bg-clip-text text-transparent mb-6 font-outfit min-h-[3rem] px-4 leading-relaxed max-w-lg">
        {displayText}
        {!typingDone && <span className="inline-block w-1 h-5 ml-1 bg-indigo-400 animate-pulse">|</span>}
      </h3>

      {/* 文本输入框容器（毛玻璃与流光边框） */}
      <div className={`w-full max-w-xl transition-all duration-300 p-[1.5px] rounded-2xl mb-6 bg-gradient-to-r ${
        isDragging ? 'from-blue-500 via-indigo-500 to-cyan-500 shadow-lg shadow-blue-500/20' : 'from-slate-200/50 to-slate-300/50'
      }`}>
        <div className="relative rounded-[15px] bg-white/90 p-4 border border-slate-200">
          <textarea
            className="w-full min-h-[120px] bg-transparent text-slate-800 placeholder-slate-400 focus:outline-none transition-all font-sans text-sm resize-none"
            placeholder="请输入您的专利特征（Claim）或拖入专利申请书/交底书文件进行评估..."
            value={claimValue}
            onChange={(e) => setClaimValue(e.target.value)}
            disabled={disabled}
          />
          {claimValue && (
            <button
              onClick={() => setClaimValue('')}
              className="absolute right-3 top-3 p-1 rounded-full hover:bg-slate-100 text-slate-500 hover:text-slate-600 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <div className="text-[10px] text-slate-400 text-right mt-1 font-mono">
            支持拖入 .txt / .md 文件解析
          </div>
        </div>
      </div>

      {/* 平滑 Morphing 三步指引 */}
      <div className="w-full max-w-xl overflow-hidden">
        <AnimatePresence initial={false}>
          {typingDone && !isCollapsed && (
            <motion.div
              initial={{ height: 0, opacity: 0, scale: 0.95 }}
              animate={{ height: 'auto', opacity: 1, scale: 1 }}
              exit={{ height: 0, opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1.0] }}
              className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left mb-6"
            >
              <div className="p-4 rounded-xl bg-white/80 border border-slate-200 hover:border-slate-350 transition-colors duration-300 flex flex-col justify-between">
                <span className="text-[10px] font-semibold text-blue-600 uppercase tracking-wider mb-1 block">第 1 步</span>
                <span className="text-xs text-slate-600 leading-normal">① 拖入文档或输入 Claim</span>
              </div>
              <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-200 hover:border-slate-700/80 transition-colors duration-300 flex flex-col justify-between">
                <span className="text-[10px] font-semibold text-indigo-600 uppercase tracking-wider mb-1 block">第 2 步</span>
                <span className="text-xs text-slate-600 leading-normal">② 观察 Agent 推理辩论与黑板特征矩阵</span>
              </div>
              <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-200 hover:border-slate-700/80 transition-colors duration-300 flex flex-col justify-between">
                <span className="text-[10px] font-semibold text-cyan-600 uppercase tracking-wider mb-1 block">第 3 步</span>
                <span className="text-xs text-slate-600 leading-normal">③ 必要时介入批注冲突并一键 Resume</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 开始专利分析评估按钮 */}
      <button 
        className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold px-8 py-3.5 rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-300 shadow-lg shadow-blue-500/25 active:scale-95 text-sm"
        onClick={handleSubmit}
        disabled={disabled}
      >
        开始专利分析评估
      </button>
    </div>
  );
}


