/**
 * Memory entry type and backend interface.
 */

export interface MemoryEntry {
  id: string;
  text: string;
  summary: string;
  tags: string[];
  category: string;
  hash: string;
  createdAt: number;
  reinforcements: number;
  metadata?: Record<string, unknown>;
}

export interface MemoryBackend {
  store(entry: MemoryEntry): void;
  getAll(): MemoryEntry[];
  getById(id: string): MemoryEntry | undefined;
  reinforce(id: string): void;
  remove(id: string): boolean;
  clear(): void;
  exportAll(): string;
  importAll(data: string): number;
}
