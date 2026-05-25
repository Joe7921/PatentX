import React, { useState } from 'react';
import { AlertCircle } from 'lucide-react';

interface AgenticPauseCardProps {
  message?: string;
  onApprove?: () => void;
  onRevise?: (details: string) => void;
}

export default function AgenticPauseCard({ message = "Agent requires human input to proceed.", onApprove, onRevise }: AgenticPauseCardProps) {
  const [details, setDetails] = useState('');

  return (
    <div className="p-4 border border-orange-200 bg-orange-50 rounded-lg flex items-start space-x-3">
      <AlertCircle className="w-6 h-6 text-orange-500 mt-0.5" />
      <div className="w-full">
        <h3 className="text-orange-800 font-semibold mb-1">Human Intervention Required</h3>
        <p className="text-orange-700 text-sm mb-3">{message}</p>
        <textarea
          className="w-full p-2 mb-3 border rounded text-sm"
          placeholder="Add revision details here..."
          value={details}
          onChange={(e) => setDetails(e.target.value)}
        />
        <div className="flex space-x-2">
          <button 
            onClick={() => onApprove && onApprove()}
            className="px-3 py-1 bg-orange-500 text-white text-sm rounded hover:bg-orange-600 transition"
          >
            Approve
          </button>
          <button 
            onClick={() => onRevise && onRevise(details)}
            className="px-3 py-1 bg-white border border-orange-300 text-orange-700 text-sm rounded hover:bg-orange-100 transition"
          >
            Revise
          </button>
        </div>
      </div>
    </div>
  );
}
