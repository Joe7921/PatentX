import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { MessageSquare } from 'lucide-react';
import { getAgentTheme } from '../../store/agenticTypes';
import { useStore } from '../../store/useStore';

interface DebateLogPanelProps {
  debateLogs: string[];
  activeFeatureId: string | null;
}

export default function DebateLogPanel({ debateLogs, activeFeatureId }: DebateLogPanelProps) {
  const { step } = useStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [debateLogs.length]);

  const parseDebateLog = (log: string) => {
    let role = "系统/专家";
    let roleKey = "system";
    let model = "";
    let content = log;
    let isSystem = true;

    const modelRegex = /\[(?:MOCK\s+)?([a-zA-Z0-9.\-_]+)(?:\s+\([^)]+\))?\]|\[[a-zA-Z0-9.\-_]+\s+\(([^)]+)\)\]/;
    const modelMatch = log.match(modelRegex);
    if (modelMatch) {
      model = modelMatch[1] || modelMatch[2];
    }

    if (log.includes("法官")) {
      role = "法官 Agent";
      roleKey = "chairman";
      isSystem = false;
    } else if (log.includes("审查员") || log.includes("examiner")) {
      role = "新颖性审查员";
      roleKey = "first_examiner";
      isSystem = false;
    } else if (log.includes("申请人") || log.includes("applicant")) {
      role = "申请人代理";
      roleKey = "applicant_representative";
      isSystem = false;
    } else if (log.includes("专家") || log.includes("expert")) {
      role = "人类专家";
      roleKey = "expert";
      isSystem = false;
      model = "Expert";
    }

    let cleanContent = log.replace(/\[[^\]]+\]\s*/g, '');
    const colonIndex = Math.max(
      cleanContent.indexOf("判定："),
      cleanContent.indexOf("判定:"),
      cleanContent.indexOf("发言："),
      cleanContent.indexOf("发言:"),
      cleanContent.indexOf("意见："),
      cleanContent.indexOf("意见:"),
      cleanContent.indexOf("裁定："),
      cleanContent.indexOf("裁定:"),
      cleanContent.indexOf("："),
      cleanContent.indexOf(":")
    );

    if (colonIndex !== -1) {
      let offset = 1;
      if (["判定：", "判定:", "发言：", "发言:", "意见：", "意见:", "裁定：", "裁定:"].some(k => cleanContent.indexOf(k) === colonIndex)) {
        offset = 3;
      }
      const candidateContent = cleanContent.slice(colonIndex + offset).trim();
      if (candidateContent.length > 0) content = candidateContent;
      else content = cleanContent.trim();
    } else {
      content = cleanContent.trim();
    }

    if (log.includes("启动评估议程") || log.includes("唤醒决策流") || log.includes("遵从专家决策更新了")) {
      isSystem = true;
      role = "系统通知";
      content = log.replace(/\[[^\]]+\]\s*/g, '').trim();
    }

    return { role, roleKey, model, content, isSystem };
  };

  return (
    <div className={`lg:col-span-1 space-y-4 flex flex-col transition-all duration-500 ${
      step === 'PAUSED' ? 'opacity-30 blur-[0.5px] pointer-events-none' : ''
    }`}>
      <h3 className="text-lg font-bold text-slate-850 font-outfit flex items-center gap-2">
        <MessageSquare className="w-5 h-5 text-cyan-400" />
        多智能体嵌套辩论日志
      </h3>
      
      <div 
        ref={scrollRef}
        className="flex-1 rounded-2xl border border-slate-200 bg-white/90 p-4 space-y-4 max-h-[550px] overflow-y-auto custom-scrollbar shadow-inner"
      >
        {debateLogs.length === 0 ? (
          <div className="text-slate-500 text-xs text-center py-8">暂无辩论日志</div>
        ) : (
          debateLogs.map((log: string, idx: number) => {
            const { role, roleKey, model, content, isSystem } = parseDebateLog(log);
            const hasActiveFeature = activeFeatureId ? log.includes(activeFeatureId) : false;
            const isDimmed = activeFeatureId && !hasActiveFeature;
            
            if (isSystem) {
              return (
                <motion.div 
                  key={idx} 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: isDimmed ? 0.35 : 1, y: 0 }}
                  transition={{ duration: 0.25 }}
                  className="text-center py-2 px-3 rounded-xl bg-slate-900/30 border border-slate-200 text-slate-500 text-[11px] font-mono leading-relaxed"
                >
                  {content}
                </motion.div>
              );
            }

            const theme = getAgentTheme(roleKey);
            const activeStyle = hasActiveFeature 
              ? "shadow-[0_0_15px_rgba(56,189,248,0.2)] border-blue-500/40 bg-blue-950/20 scale-[1.01]" 
              : "";

            return (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: isDimmed ? 0.35 : 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className={`flex items-start gap-3 p-3.5 rounded-2xl border transition-all duration-300 ${theme.bgClass} ${theme.borderClass} ${activeStyle}`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border shrink-0 bg-white ${theme.textClass} ${theme.borderClass}`}>
                  {role.charAt(0)}
                </div>
                <div className="flex-1 space-y-1.5 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className={`text-xs font-bold ${theme.textClass}`}>{role}</span>
                    {model && (
                      <span className="px-1.5 py-0.5 rounded text-[9px] bg-white border border-slate-200 text-slate-600 font-mono shadow-sm">
                        {model}
                      </span>
                    )}
                  </div>
                  <p className="text-xs leading-relaxed text-slate-800 break-words">{content}</p>
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
}
