import React from 'react';

export default function ThinkingIndicator({ step = "正在分析专利交底书" }: { step?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 space-y-6 text-center">
      <div className="relative w-16 h-16">
        <div className="absolute inset-0 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
        <div className="absolute inset-2 border-4 border-purple-500/20 border-b-purple-500 rounded-full animate-[spin_1.5s_linear_infinite_reverse]"></div>
      </div>
      <div className="space-y-2">
        <h4 className="text-lg font-bold text-slate-850 font-outfit tracking-wide animate-pulse">
          智能体思考中
        </h4>
        <p className="text-slate-600 text-sm max-w-xs transition-all duration-300">
          {step}
        </p>
      </div>
    </div>
  );
}

