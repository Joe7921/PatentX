import React from 'react';
import { Upload } from 'lucide-react';

interface UploadHubProps {
  onUpload?: () => void;
}

export default function UploadHub({ onUpload }: UploadHubProps) {
  return (
    <div className="p-6 border-2 border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center bg-gray-50">
      <Upload className="w-12 h-12 text-gray-400 mb-4" />
      <p className="text-gray-600 mb-2">Drag and drop files here</p>
      <button 
        onClick={onUpload}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
      >
        Simulate Upload & Start
      </button>
    </div>
  );
}
