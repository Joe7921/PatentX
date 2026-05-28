import React from 'react';
import { Menu, MessageSquare, History, Settings, HelpCircle } from 'lucide-react';

export default function Sidebar() {
  return (
    <div className="fixed left-0 top-0 bottom-0 w-[56px] bg-[#F7F9FC] border-r border-[#E3E8EE] flex flex-col items-center py-4 z-50">
      <button className="p-2.5 text-[#5F6368] hover:bg-[#E8EAED] rounded-full transition-colors mb-6">
        <Menu className="w-5 h-5" />
      </button>
      
      <div className="flex flex-col gap-2 w-full px-2">
        <button className="p-2.5 text-[#5F6368] hover:bg-[#E8EAED] rounded-full transition-colors mx-auto relative group">
          <MessageSquare className="w-5 h-5" />
          <span className="absolute left-full ml-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 whitespace-nowrap pointer-events-none transition-opacity">新对话</span>
        </button>
        <button className="p-2.5 text-[#5F6368] hover:bg-[#E8EAED] rounded-full transition-colors mx-auto relative group">
          <History className="w-5 h-5" />
          <span className="absolute left-full ml-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 whitespace-nowrap pointer-events-none transition-opacity">历史记录</span>
        </button>
      </div>

      <div className="mt-auto flex flex-col gap-2 w-full px-2">
        <button className="p-2.5 text-[#5F6368] hover:bg-[#E8EAED] rounded-full transition-colors mx-auto relative group">
          <HelpCircle className="w-5 h-5" />
          <span className="absolute left-full ml-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 whitespace-nowrap pointer-events-none transition-opacity">帮助</span>
        </button>
        <button className="p-2.5 text-[#5F6368] hover:bg-[#E8EAED] rounded-full transition-colors mx-auto relative group">
          <Settings className="w-5 h-5" />
          <span className="absolute left-full ml-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 whitespace-nowrap pointer-events-none transition-opacity">设置</span>
        </button>
      </div>
    </div>
  );
}
