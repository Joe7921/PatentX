import React from 'react';
import { AlertCircle } from 'lucide-react';

interface AgenticPauseCardProps {
  message?: string;
  onResume: () => void;
}

export default function AgenticPauseCard({ message = "Agent requires human input to proceed.", onResume }: AgenticPauseCardProps) {
  return (
    <div className="p-4 border border-orange-200 bg-orange-50 rounded-lg flex items-start space-x-3">
      <AlertCircle className="w-6 h-6 text-orange-500 mt-0.5" />
      <div>
        <h3 className="text-orange-800 font-semibold mb-1">Human Intervention Required</h3>
        <p className="text-orange-700 text-sm mb-3">{message}</p>
        <div className="flex space-x-2">
          <button 
            className="px-3 py-1 bg-orange-500 text-white text-sm rounded hover:bg-orange-600 transition"
            onClick={onResume}
          >
            Provide Input / Resume
          </button>
        </div>
      </div>
    </div>
  );
}
