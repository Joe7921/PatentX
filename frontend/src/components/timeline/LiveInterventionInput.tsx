import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquarePlus, Send, X, Loader2 } from 'lucide-react';

interface Props {
  onSubmit: (msg: string) => Promise<boolean> | void;
  isSubmitting?: boolean;
}

export default function LiveInterventionInput({ onSubmit, isSubmitting }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [text, setText] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!text.trim() || isSubmitting) return;
    
    await onSubmit(text);
    setText('');
    setIsOpen(false);
  };

  return (
    <div className="relative mt-2 mb-1 w-full max-w-sm">
      <AnimatePresence mode="wait">
        {!isOpen ? (
          <motion.button
            key="button"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.1 } }}
            onClick={() => setIsOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/50 backdrop-blur-sm border border-gemini-outline/50 shadow-sm text-xs text-slate-500 hover:text-blue-600 hover:border-blue-200 hover:bg-white transition-all cursor-pointer group"
          >
            <MessageSquarePlus className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" />
            <span>随时打断补充...</span>
          </motion.button>
        ) : (
          <motion.form
            key="form"
            initial={{ opacity: 0, y: -5, height: 0 }}
            animate={{ opacity: 1, y: 0, height: 'auto' }}
            exit={{ opacity: 0, y: -5, height: 0, transition: { duration: 0.15 } }}
            onSubmit={handleSubmit}
            className="relative flex items-center bg-white border border-blue-200 rounded-lg shadow-gemini-md overflow-hidden"
          >
            <input
              ref={inputRef}
              type="text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="输入打断指令或补充事实给Agent..."
              disabled={isSubmitting}
              className="flex-1 text-sm py-2.5 pl-3 pr-16 outline-none text-slate-700 bg-transparent placeholder-slate-400"
            />
            <div className="absolute right-1 flex items-center gap-0.5">
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                disabled={isSubmitting}
                className="p-1.5 text-slate-400 hover:text-slate-600 transition-colors rounded-md hover:bg-slate-50"
              >
                <X className="w-4 h-4" />
              </button>
              <button
                type="submit"
                disabled={!text.trim() || isSubmitting}
                className={`p-1.5 rounded-md transition-colors ${text.trim() && !isSubmitting ? 'text-blue-600 hover:bg-blue-50' : 'text-slate-300'}`}
              >
                {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </div>
          </motion.form>
        )}
      </AnimatePresence>
    </div>
  );
}
