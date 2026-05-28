import React, { useState } from 'react';
import { Mic, Plus } from 'lucide-react';
import { motion } from 'framer-motion';

interface UploadHubProps {
  onUpload: (claimText: string) => void;
  disabled?: boolean;
}

export default function UploadHub({ onUpload, disabled = false }: UploadHubProps) {
  const [claimValue, setClaimValue] = useState("");

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!disabled && claimValue.trim()) {
      onUpload(claimValue.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className={`w-full flex flex-col items-center justify-center transition-all ${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
      {/* 极简 Gemini 风格的输入胶囊 */}
      <motion.form 
        onSubmit={handleSubmit}
        className="w-full relative flex items-center bg-[#F0F4F9] rounded-full px-4 py-3 shadow-[0_4px_12px_rgba(0,0,0,0.05)] border border-transparent focus-within:bg-white focus-within:shadow-[0_4px_16px_rgba(0,0,0,0.1)] focus-within:border-blue-200 transition-all duration-300"
      >
        <button type="button" className="p-2 text-[#5F6368] hover:bg-[#E8EAED] rounded-full transition-colors flex-shrink-0">
          <Plus className="w-5 h-5" />
        </button>
        
        <input
          type="text"
          className="flex-1 bg-transparent border-none outline-none px-3 text-[#1F1F1F] placeholder-[#5F6368] text-[15px]"
          placeholder="描述你的发明，或上传交底书..."
          value={claimValue}
          onChange={(e) => setClaimValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
        />
        
        <button type="button" className="p-2 text-[#5F6368] hover:bg-[#E8EAED] rounded-full transition-colors flex-shrink-0">
          <Mic className="w-5 h-5" />
        </button>
      </motion.form>

      <div className="mt-4 text-[12px] text-[#5F6368] tracking-wide text-center">
        支持拖入 .txt / .md 文件 · 按 Enter 发送 · Shift+Enter 换行
      </div>
    </div>
  );
}
