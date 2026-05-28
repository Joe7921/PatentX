import React from 'react';
import { FileText, Download, Share2 } from 'lucide-react';
import { useStore } from '../store/useStore';

export default function DocumentPreview() {
  const { claim } = useStore();

  return (
    <div className="flex flex-col h-full bg-white rounded-2xl shadow-sm border border-gray-100">
      <div className="flex items-center justify-between p-4 border-b border-gray-100">
        <div className="flex items-center gap-2 text-slate-700">
          <FileText className="w-5 h-5 text-blue-500" />
          <h2 className="font-medium text-sm">交底书特征萃取与评估分析报告</h2>
        </div>
        <div className="flex items-center gap-2 text-slate-500">
          <button className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors">
            <Share2 className="w-4 h-4" />
          </button>
          <button className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors">
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      <div className="flex-1 p-6 overflow-y-auto prose prose-sm max-w-none text-slate-600">
        {!claim ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400">
            <div className="w-16 h-16 bg-slate-50 rounded-2xl flex items-center justify-center mb-4 border border-slate-100">
              <FileText className="w-8 h-8 text-slate-300" />
            </div>
            <p>特征分析报告将在此实时生成...</p>
          </div>
        ) : (
          <div className="animate-fade-in">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">技术特征提炼</h3>
            <div className="bg-blue-50/50 rounded-xl p-4 border border-blue-100/50 text-slate-700 mb-6">
              {claim}
            </div>
            
            <h3 className="text-lg font-semibold text-slate-800 mb-4 mt-8">Agent 评估进展</h3>
            <div className="space-y-4">
               {/* 骨架屏占位 */}
               <div className="h-4 bg-slate-100 rounded w-3/4 animate-pulse"></div>
               <div className="h-4 bg-slate-100 rounded w-full animate-pulse"></div>
               <div className="h-4 bg-slate-100 rounded w-5/6 animate-pulse"></div>
               <div className="h-4 bg-slate-100 rounded w-2/3 animate-pulse"></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
