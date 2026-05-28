import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import React from 'react';
import { render, screen, cleanup, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import DynamicTopoGraph from '../src/components/DynamicTopoGraph';
import DraftingPiP from '../src/components/DraftingPiP';
import { useStore } from '../src/store/useStore';

// Mock IntersectionObserver for Framer Motion
const mockIntersectionObserver = class {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
};
window.IntersectionObserver = mockIntersectionObserver as any;

describe('Dynamic Topo UI Verification', () => {
  beforeEach(() => {
    // Reset store before each test
    act(() => {
      useStore.setState({
        agenticState: {
          phases: [],
          currentPhase: 0,
          topologyNodes: [],
          topologyEdges: [],
          votes: [],
          hitlActive: false,
          hitlReason: '',
          isCompleted: false,
        },
        documentChunks: [],
        isDraftingComplete: false,
      });
    });
  });

  afterEach(() => {
    cleanup();
  });

  it('renders DynamicTopoGraph with numerous nodes and extremely long text', () => {
    const manyNodes = [];
    for (let i = 0; i < 200; i++) {
      manyNodes.push({
        id: `node_${i}`,
        type: i % 2 === 0 ? 'agent' : 'tool',
        status: i === 199 ? 'active' : 'completed',
        label: `AgentOrTool_${i}`,
        agentId: `Agent_${i}`,
        content: 'This is a very very long content string that should be truncated or scrolled depending on the UI. '.repeat(100), // Very long content
        parentId: i > 0 ? `node_${i - 1}` : 'root',
        timestamp: Date.now() + i,
      });
    }

    act(() => {
      useStore.setState(state => ({
        ...state,
        agenticState: {
          ...state.agenticState,
          topologyNodes: manyNodes as any
        }
      }));
    });

    const { container } = render(<DynamicTopoGraph />);
    
    // Validate that the graph renders without crashing and some nodes are present
    expect(screen.getByText('AgentOrTool_0')).toBeInTheDocument();
    expect(screen.getByText('AgentOrTool_199')).toBeInTheDocument();
  });

  it('renders DraftingPiP with numerous document chunks', () => {
    const chunks = [];
    for (let i = 0; i < 5000; i++) {
      chunks.push(`Chunk_number_${i} `);
    }

    act(() => {
      useStore.setState({
        documentChunks: chunks,
        isDraftingComplete: false,
      });
    });

    render(<DraftingPiP />);
    
    // PiP should be visible
    expect(screen.getByText('Agent 正在起草...')).toBeInTheDocument();
    
    // Simulate expand
    const pipTrigger = screen.getByText('Agent 正在起草...').closest('div')?.parentElement?.parentElement;
    expect(pipTrigger).not.toBeNull();
    act(() => {
      pipTrigger!.click();
    });

    // Check content
    expect(screen.getByText(/Chunk_number_0/)).toBeInTheDocument();
    expect(screen.getByText(/Chunk_number_4999/)).toBeInTheDocument();
  });
});
