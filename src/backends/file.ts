import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'fs';
import { dirname, join } from 'path';
import { MemoryBackend, MemoryEntry } from './types';

export class FileBackend implements MemoryBackend {
  private entries: Map<string, MemoryEntry> = new Map();

  constructor(private filePath: string) {
    if (existsSync(filePath)) {
      const data = JSON.parse(readFileSync(filePath, 'utf-8'));
      for (const e of data) this.entries.set(e.id, e);
    }
  }

  private save(): void {
    mkdirSync(dirname(this.filePath), { recursive: true });
    writeFileSync(this.filePath, JSON.stringify([...this.entries.values()], null, 2));
  }

  store(entry: MemoryEntry): void { this.entries.set(entry.id, entry); this.save(); }
  getAll(): MemoryEntry[] { return [...this.entries.values()]; }
  getById(id: string): MemoryEntry | undefined { return this.entries.get(id); }
  reinforce(id: string): void {
    const e = this.entries.get(id);
    if (e) { e.reinforcements++; this.save(); }
  }
  remove(id: string): boolean { const r = this.entries.delete(id); if (r) this.save(); return r; }
  clear(): void { this.entries.clear(); this.save(); }
  exportAll(): string { return JSON.stringify([...this.entries.values()]); }
  importAll(data: string): number {
    const items: MemoryEntry[] = JSON.parse(data);
    for (const e of items) this.entries.set(e.id, e);
    this.save();
    return items.length;
  }
}
