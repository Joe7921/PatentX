import React, { useState, useEffect } from 'react';
import UploadHub from './UploadHub';
import ThinkingIndicator from './ThinkingIndicator';
import AgenticPauseCard from './AgenticPauseCard';

type State = 'IDLE' | 'STREAMING' | 'PAUSED' | 'COMPLETED' | 'ERROR';

export default function DiagnosticDashboard() {
  const [appState, setAppState] = useState<State>('IDLE');
  const [messages, setMessages] = useState<string[]>([]);
  const [interruptId, setInterruptId] = useState<string | null>(null);

  const startAnalysis = () => {
    setAppState('STREAMING');
    setMessages([]);
    setInterruptId(null);

    const eventSource = new EventSource('http://localhost:8000/api/v1/analyze/stream');

    eventSource.addEventListener('node_start', (e: any) => {
      const data = JSON.parse(e.data);
      setMessages((prev) => [...prev, data.message]);
    });

    eventSource.addEventListener('hitl_interrupt', (e: any) => {
      const data = JSON.parse(e.data);
      setMessages((prev) => [...prev, data.message]);
      setInterruptId(data.id);
      setAppState('PAUSED');
      // Connection stays open
    });

    eventSource.addEventListener('completed', (e: any) => {
      const data = JSON.parse(e.data);
      setMessages((prev) => [...prev, data.message]);
      setAppState('COMPLETED');
      eventSource.close();
    });

    eventSource.addEventListener('error', () => {
      setAppState('ERROR');
      eventSource.close();
    });
  };

  const resumeAnalysis = async () => {
    if (!interruptId) return;
    try {
      const res = await fetch(`http://localhost:8000/api/v1/evaluation/${interruptId}/resume`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'approve', details: 'User approved' })
      });
      if (res.ok) {
        setAppState('STREAMING');
        setInterruptId(null);
      }
    } catch (err) {
      console.error('Failed to resume', err);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <header className="mb-8 border-b pb-4">
        <h1 className="text-3xl font-bold text-gray-900">PatentX Diagnostic Dashboard</h1>
        <p className="text-gray-500 mt-2">Monitor AI workflow and system metrics</p>
      </header>

      <section>
        <h2 className="text-xl font-semibold mb-4 text-gray-800">1. Upload Source Material</h2>
        <UploadHub onUpload={startAnalysis} disabled={appState !== 'IDLE'} />
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h2 className="text-xl font-semibold mb-4 text-gray-800">System Activity</h2>
          <div className="space-y-4">
            {appState === 'STREAMING' && <ThinkingIndicator step="Processing stream..." />}
            
            {appState === 'PAUSED' && (
              <AgenticPauseCard 
                message="Ambiguous phrase found. Please clarify." 
                onResume={resumeAnalysis} 
              />
            )}
            
            {messages.length > 0 && (
              <div className="bg-gray-100 p-4 rounded text-sm space-y-2">
                <h3 className="font-semibold text-gray-700">Event Log:</h3>
                {messages.map((msg, i) => (
                  <div key={i} className="text-gray-600">- {msg}</div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-4 text-gray-800">Pipeline Status</h2>
          <div className="bg-white border rounded-lg p-4 shadow-sm">
            <ul className="space-y-3 text-sm">
              <li className="flex justify-between border-b pb-2">
                <span className="text-gray-600">Document Parsing</span>
                <span className={appState !== 'IDLE' ? "text-green-600 font-medium" : "text-gray-400"}>
                  {appState !== 'IDLE' ? 'Complete' : 'Pending'}
                </span>
              </li>
              <li className="flex justify-between border-b pb-2">
                <span className="text-gray-600">Entity Extraction</span>
                {appState === 'STREAMING' ? (
                  <span className="text-blue-600 font-medium animate-pulse">In Progress...</span>
                ) : appState === 'PAUSED' ? (
                  <span className="text-orange-500 font-medium">Paused</span>
                ) : appState === 'COMPLETED' ? (
                  <span className="text-green-600 font-medium">Complete</span>
                ) : (
                  <span className="text-gray-400 font-medium">Pending</span>
                )}
              </li>
              <li className="flex justify-between">
                <span className="text-gray-600">Report Generation</span>
                <span className={appState === 'COMPLETED' ? "text-green-600 font-medium" : "text-gray-400"}>
                  {appState === 'COMPLETED' ? 'Complete' : 'Pending'}
                </span>
              </li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}
