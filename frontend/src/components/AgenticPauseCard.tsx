import React, { useState } from 'react';
import { AlertCircle } from 'lucide-react';

export default function AgenticPauseCard({ 
  message = "智能体评估遭遇争议，需要人类专家介入决策。", 
  onResume 
}: { 
  message?: string, 
  onResume?: (action: 'Approve' | 'Revise', details: string) => void 
}) {
  const [details, setDetails] = useState('');

  return (
    <div className="flex flex-col space-y-5 py-2">
      <div className="flex items-start space-x-4">
        <div className="p-3 bg-amber-500/20 text-amber-400 rounded-xl">
          <AlertCircle className="w-6 h-6" />
        </div>
        <div>
          <h3 className="text-amber-400 font-bold text-lg font-outfit mb-1">需要人类专家审查 (HITL)</h3>
          <p className="text-slate-600 text-sm leading-relaxed">{message}</p>
        </div>
      </div>
      
      <div className="flex flex-col space-y-3 pt-2">
        <textarea 
          id="global-pause-textarea"
          value={details}
          onChange={(e) => setDetails(e.target.value)}
          placeholder="在此输入专家修正意见或裁决理由..." 
          rows={3}
          className="w-full bg-white/90 border border-slate-200 text-slate-850 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/50 transition resize-none placeholder-slate-400"
        />
        
        <div className="flex space-x-3 justify-end pt-1">
          <button 
            onClick={() => onResume?.('Revise', details)}
            className="px-5 py-2.5 bg-slate-100 text-slate-700 text-sm font-semibold rounded-xl hover:bg-slate-200 transition-all border border-slate-200 active:scale-95">
            专家修正 (Revise)
          </button>
          <button 
            onClick={() => onResume?.('Approve', details)}
            className="px-5 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 text-slate-950 text-sm font-bold rounded-xl hover:from-amber-600 hover:to-orange-600 transition-all shadow-lg shadow-amber-500/20 active:scale-95">
            批准通过 (Approve)
          </button>
        </div>
      </div>
    </div>
  );
}

