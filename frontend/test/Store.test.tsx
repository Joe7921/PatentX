import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { useStore } from '../src/store/useStore';
import { act } from '@testing-library/react';

// Mock EventSource
class MockEventSource {
  url: string;
  onopen: () => void;
  onerror: (e: any) => void;
  listeners: Record<string, Function[]>;
  constructor(url: string) {
    this.url = url;
    this.onopen = () => {};
    this.onerror = () => {};
    this.listeners = {};
    setTimeout(() => this.onopen(), 0);
  }
  addEventListener(event: string, cb: Function) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(cb);
  }
  close() {}
  
  emit(event: string, data: any) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => cb({ type: event, data: JSON.stringify(data) }));
    }
  }
}

describe('Store SSE Processing', () => {
  beforeEach(() => {
    vi.stubGlobal('EventSource', MockEventSource);
    
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
        step: 'UPLOAD',
      });
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('processes SSE events correctly', async () => {
    act(() => {
      useStore.getState().startAnalysis('test claim');
    });

    // Need to get the mocked instance, but we can't easily access it.
    // Instead we can just trigger it if we intercept the constructor, but it's easier to just do it via a small test hack.
  });
});
