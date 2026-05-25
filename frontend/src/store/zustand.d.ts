declare module 'zustand' {
  export type StateCreator<T> = (
    set: (
      partial: T | Partial<T> | ((state: T) => T | Partial<T>),
      replace?: boolean
    ) => void,
    get: () => T,
    api: any
  ) => T;

  export function create<T>(): (initializer: StateCreator<T>) => any;
  export function create<T>(initializer: StateCreator<T>): any;
}
