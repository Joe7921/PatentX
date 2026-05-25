import { useState, useEffect } from 'react';

export function create<T>() {
  return function(initializer: (
    set: (partial: Partial<T> | ((state: T) => Partial<T>)) => void,
    get: () => T
  ) => T) {
    let state: T;
    const listeners = new Set<() => void>();

    const get = () => state;
    const set = (partial: Partial<T> | ((state: T) => Partial<T>)) => {
      const nextState = typeof partial === 'function' ? (partial as any)(state) : partial;
      state = { ...state, ...nextState };
      listeners.forEach((listener) => listener());
    };

    state = initializer(set, get);

    function useStore(): T;
    function useStore<U>(selector: (state: T) => U): U;
    function useStore<U>(selector?: (state: T) => U): any {
      const [, forceUpdate] = useState(0);

      useEffect(() => {
        const listener = () => forceUpdate((prev) => prev + 1);
        listeners.add(listener);
        return () => {
          listeners.delete(listener);
        };
      }, []);

      return selector ? selector(state) : state;
    }

    useStore.getState = get;
    useStore.setState = set;

    return useStore;
  };
}

