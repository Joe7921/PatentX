import React, { useState, useEffect } from 'react';
import UploadHub from './UploadHub';
import ThinkingIndicator from './ThinkingIndicator';
import AgenticPauseCard from './AgenticPauseCard';

type WorkflowState = 'IDLE' | 'STREAMING' | 'PAUSED' | 'COMPLETED';

export default function DiagnosticDashboard() {
  const [workflowState, setWorkflowState] = useState<WorkflowState>('IDLE');
  const [messages, setMessages] = useState<string[]>([]);
  const [hitlId, setHitlId] = useState<string | null>(null);

  const startAnalysis = () => {
    setWorkflowState('STREAMING');
    setMessages([]);
    setHitlId(null);

    const eventSource = new EventSource('http://localhost:8000/api/v1/analyze/stream');

    eventSource.addEventListener('node_start', (e) => {
      const data = JSON.parse(e.data);
      setMessages(prev => [...prev, data.message]);
    });

    eventSource.addEventListener('hitl_interrupt', (e) => {
      const data = JSON.parse(e.data);
      setMessages(prev => [...prev, data.message]);
      setHitlId(data.id);
      setWorkflowState('PAUSED');
    });

    eventSource.addEventListener('completed', (e) => {
      const data = JSON.parse(e.data);
      setMessages(prev => [...prev, data.message]);
      setWorkflowState('COMPLETED');
      eventSource.close();
    });

    eventSource.addEventListener('error', () => {
      setMessages(prev => [...prev, "Connection error or timeout."]);
      setWorkflowState('IDLE');
      eventSource.close();
    });
  };

  const handleResume = async (action: string, details: string) => {
    if (!hitlId) return;
    try {
      await fetch(`http://localhost:8000/api/v1/evaluation/${hitlId}/resume`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action, details })
      });
      setWorkflowState('STREAMING');
      setHitlId(null);
    } catch (err) {
      console.error("Failed to resume:", err);
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
        <UploadHub onUpload={startAnalysis} />
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h2 className="text-xl font-semibold mb-4 text-gray-800">System Activity</h2>
          <div className="space-y-4">
            {workflowState === 'STREAMING' && (
              <ThinkingIndicator step={messages[messages.length - 1] || "Processing..."} />
            )}
            {workflowState === 'PAUSED' && (
              <AgenticPauseCard 
                message={messages[messages.length - 1]}
                onApprove={() => handleResume('Approve', '')}
                onRevise={(details) => handleResume('Revise', details)}
              />
            )}
            {workflowState === 'COMPLETED' && (
              <div className="p-4 bg-green-50 text-green-800 border border-green-200 rounded-lg">
                Analysis Completed successfully!
              </div>
            )}
            {messages.length > 0 && (
              <div className="mt-4 p-4 bg-gray-50 border rounded text-sm text-gray-600 h-32 overflow-y-auto">
                {messages.map((m, i) => <div key={i}>{m}</div>)}
              </div>
            )}
          </div>
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-4 text-gray-800">Pipeline Status</h2>
          <div className="bg-white border rounded-lg p-4 shadow-sm">
            <ul className="space-y-3 text-sm">
              <li className="flex justify-between border-b pb-2">
                <span className="text-gray-600">Workflow State</span>
                <span className="font-medium text-blue-600">{workflowState}</span>
              </li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}
