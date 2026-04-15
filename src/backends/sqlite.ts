import Database from 'better-sqlite3';
import { MemoryBackend, MemoryEntry } from './types';

export class SqliteBackend implements MemoryBackend {
  private db: Database.Database;

  constructor(dbPath: string) {
    this.db = new Database(dbPath);
    this.db.exec(`CREATE TABLE IF NOT EXISTS memories (
      id TEXT PRIMARY KEY,
      text TEXT NOT NULL,
      summary TEXT NOT NULL,
      tags TEXT NOT NULL,
      category TEXT NOT NULL,
      hash TEXT NOT NULL,
      createdAt INTEGER NOT NULL,
      reinforcements INTEGER DEFAULT 0,
      metadata TEXT
    )`);
  }

  store(entry: MemoryEntry): void {
    this.db.prepare(
      `INSERT OR REPLACE INTO memories (id,text,summary,tags,category,hash,createdAt,reinforcements,metadata)
       VALUES (?,?,?,?,?,?,?,?,?)`
    ).run(entry.id, entry.text, entry.summary, JSON.stringify(entry.tags),
      entry.category, entry.hash, entry.createdAt, entry.reinforcements,
      JSON.stringify(entry.metadata || {}));
  }

  private rowToEntry(row: any): MemoryEntry {
    return { ...row, tags: JSON.parse(row.tags), metadata: JSON.parse(row.metadata || '{}') };
  }

  getAll(): MemoryEntry[] {
    return this.db.prepare('SELECT * FROM memories ORDER BY createdAt DESC').all().map(this.rowToEntry);
  }

  getById(id: string): MemoryEntry | undefined {
    const row = this.db.prepare('SELECT * FROM memories WHERE id=?').get(id) as any;
    return row ? this.rowToEntry(row) : undefined;
  }

  reinforce(id: string): void {
    this.db.prepare('UPDATE memories SET reinforcements = reinforcements + 1 WHERE id=?').run(id);
  }

  remove(id: string): boolean {
    return this.db.prepare('DELETE FROM memories WHERE id=?').run(id).changes > 0;
  }

  clear(): void { this.db.exec('DELETE FROM memories'); }

  exportAll(): string { return JSON.stringify(this.getAll()); }

  importAll(data: string): number {
    const items: MemoryEntry[] = JSON.parse(data);
    const insert = this.db.transaction((entries: MemoryEntry[]) => {
      for (const e of entries) this.store(e);
      return entries.length;
    });
    return insert(items);
  }
}
