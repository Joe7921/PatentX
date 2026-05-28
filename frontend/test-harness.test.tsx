import { describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import { useStore } from './src/store/useStore';
import DynamicTopoGraph from './src/components/DynamicTopoGraph';
import DraftingPiP from './src/components/DraftingPiP';

describe('Dynamic Topo UI Edge Cases', () => {
  it('handles extremely long texts in DraftingPiP', async () => {
    // Reset store
    useStore.setState({
      documentChunks: [],
      isDraftingComplete: false,
    });

    const numChunks = 10000;
    const chunkContent = 'This is a long piece of text representing a single chunk. ';
    
    // Simulate streaming chunks
    const startTime = performance.now();
    for (let i = 0; i < numChunks; i++) {
      useStore.setState((state) => ({
        documentChunks: [...state.documentChunks, chunkContent]
      }));
    }
    const storeTime = performance.now();
    console.log(`Store updated with ${numChunks} chunks in ${storeTime - startTime}ms`);

    const renderStart = performance.now();
    const { container } = render(<DraftingPiP />);
    const renderEnd = performance.now();
    console.log(`DraftingPiP rendered in ${renderEnd - renderStart}ms`);

    expect(container).toBeTruthy();
  });

  it('handles lots of nodes in DynamicTopoGraph', () => {
    // Reset store
    useStore.setState({
      agenticState: {
        phases: [],
        currentPhase: 1,
        topologyNodes: [],
        topologyEdges: [],
        hitlActive: false,
        hitlReason: '',
        hitlAfterPhase: undefined,
        votingPhaseId: undefined,
        votes: [],
        isCompleted: false,
        legalExaminerSummoned: false,
      }
    });

    const numNodes = 5000;
    
    // Simulate many node additions
    const startTime = performance.now();
    for (let i = 0; i < numNodes; i++) {
      useStore.setState((state) => {
        const agSt = state.agenticState;
        return {
          agenticState: {
            ...agSt,
            topologyNodes: [
              ...agSt.topologyNodes,
              {
                id: `node_${i}`,
                type: 'agent',
                status: 'completed',
                label: `Agent ${i}`,
                parentId: 'phase_1',
                timestamp: Date.now()
              }
            ]
          }
        };
      });
    }
    const storeTime = performance.now();
    console.log(`Store updated with ${numNodes} nodes in ${storeTime - startTime}ms`);

    const renderStart = performance.now();
    const { container } = render(<DynamicTopoGraph />);
    const renderEnd = performance.now();
    console.log(`DynamicTopoGraph rendered in ${renderEnd - renderStart}ms`);

    expect(container).toBeTruthy();
  });
});
