/**
 * Core memory manager — ties together extraction, dedup, storage, and retrieval.
 */
import { randomUUID } from 'crypto';
import { MemoryBackend, MemoryEntry } from './backends/types';
import { extractContext } from './extractor';
import { contentHash, isDuplicate } from './dedup';
import { rankByRelevance, ScoredResult } from './retrieval';

export interface StoreOptions {
  tags?: string[];
  category?: string;
  metadata?: Record<string, unknown>;
  dedupThreshold?: number;
}

export class MemoryManager {
  constructor(private backend: MemoryBackend) {}

  store(text: string, opts: StoreOptions = {}): MemoryEntry | null {
    const all = this.backend.getAll();
    const threshold = opts.dedupThreshold ?? 0.85;

    if (isDuplicate(text, all.map(e => e.text), threshold)) {
      // Reinforce existing similar memory instead
      const hash = contentHash(text);
      const existing = all.find(e => e.hash === hash);
      if (existing) this.backend.reinforce(existing.id);
      return null;
    }

    const ctx = extractContext(text);
    const entry: MemoryEntry = {
      id: randomUUID(),
      text,
      summary: ctx.summary,
      tags: [...new Set([...ctx.tags, ...(opts.tags || [])])],
      category: opts.category || ctx.category,
      hash: contentHash(text),
      createdAt: Date.now(),
      reinforcements: 0,
      metadata: opts.metadata,
    };

    this.backend.store(entry);
    return entry;
  }

  recall(query: string, limit = 10): ScoredResult<MemoryEntry>[] {
    const all = this.backend.getAll();
    const ranked = rankByRelevance(query, all.map(e => ({
      text: e.text,
      createdAt: e.createdAt,
      reinforcements: e.reinforcements,
      data: e,
    })));
    return ranked.slice(0, limit);
  }

  list(): MemoryEntry[] {
    return this.backend.getAll();
  }

  remove(id: string): boolean {
    return this.backend.remove(id);
  }

  reinforce(id: string): void {
    this.backend.reinforce(id);
  }

  clear(): void {
    this.backend.clear();
  }

  exportMemories(): string {
    return this.backend.exportAll();
  }

  importMemories(data: string): number {
    return this.backend.importAll(data);
  }
}
