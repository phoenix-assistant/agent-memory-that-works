import { MemoryManager } from '../src/memory';
import { FileBackend } from '../src/backends/file';
import { extractContext } from '../src/extractor';
import { contentHash, similarity, isDuplicate } from '../src/dedup';
import { tfidfScore, decayScore } from '../src/retrieval';
import { mkdtempSync, rmSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

describe('dedup', () => {
  test('contentHash is deterministic', () => {
    expect(contentHash('hello world')).toBe(contentHash('hello world'));
    expect(contentHash('Hello World')).toBe(contentHash('hello world'));
  });

  test('similarity scores identical texts as 1', () => {
    expect(similarity('auth pattern', 'auth pattern')).toBe(1);
  });

  test('similarity scores different texts low', () => {
    expect(similarity('auth pattern', 'banana smoothie recipe')).toBeLessThan(0.3);
  });

  test('isDuplicate catches exact matches', () => {
    expect(isDuplicate('hello', ['hello', 'world'])).toBe(true);
  });

  test('isDuplicate catches similar text', () => {
    expect(isDuplicate('the auth pattern uses JWT tokens', [
      'the authentication pattern uses JWT tokens for auth'
    ], 0.5)).toBe(true);
  });
});

describe('extractor', () => {
  test('extracts decision category', () => {
    const ctx = extractContext('We decided to use PostgreSQL for the database');
    expect(ctx.category).toBe('decision');
    expect(ctx.tags).toContain('decision');
  });

  test('extracts code category', () => {
    const ctx = extractContext('export function getData() { return fetch("/api") }');
    expect(ctx.category).toBe('code');
  });

  test('extracts hashtags', () => {
    const ctx = extractContext('Important note #auth #security');
    expect(ctx.tags).toContain('auth');
    expect(ctx.tags).toContain('security');
  });
});

describe('retrieval', () => {
  test('tfidfScore ranks relevant docs higher', () => {
    const scores = tfidfScore('auth patterns', [
      'authentication patterns and best practices',
      'banana smoothie recipe for summer',
      'auth middleware pattern in express',
    ]);
    expect(scores[0]).toBeGreaterThan(scores[1]);
    expect(scores[2]).toBeGreaterThan(scores[1]);
  });

  test('decayScore reduces with age', () => {
    const fresh = decayScore(1.0, 0);
    const old = decayScore(1.0, 30 * 24 * 60 * 60 * 1000); // 30 days
    expect(fresh).toBeGreaterThan(old);
    expect(old).toBeCloseTo(0.5, 1);
  });

  test('reinforcement boosts score', () => {
    const base = decayScore(1.0, 1000, 30, 0);
    const boosted = decayScore(1.0, 1000, 30, 3);
    expect(boosted).toBeGreaterThan(base);
  });
});

describe('MemoryManager (file backend)', () => {
  let dir: string;
  let manager: MemoryManager;

  beforeEach(() => {
    dir = mkdtempSync(join(tmpdir(), 'agentmem-test-'));
    manager = new MemoryManager(new FileBackend(join(dir, 'mem.json')));
  });

  afterEach(() => {
    rmSync(dir, { recursive: true, force: true });
  });

  test('store and list', () => {
    manager.store('Always use kebab-case for file names');
    const all = manager.list();
    expect(all).toHaveLength(1);
    expect(all[0].text).toContain('kebab-case');
  });

  test('dedup prevents duplicates', () => {
    manager.store('Use JWT for authentication');
    const r = manager.store('Use JWT for authentication');
    expect(r).toBeNull();
    expect(manager.list()).toHaveLength(1);
  });

  test('recall returns relevant results', () => {
    manager.store('Authentication uses JWT tokens with RS256');
    manager.store('Database migrations run on deploy');
    manager.store('CSS grid is preferred over flexbox for layouts');
    const results = manager.recall('JWT authentication');
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].item.text).toContain('JWT');
  });

  test('export and import', () => {
    manager.store('Memory one');
    manager.store('Memory two');
    const exported = manager.exportMemories();

    const dir2 = mkdtempSync(join(tmpdir(), 'agentmem-test2-'));
    const manager2 = new MemoryManager(new FileBackend(join(dir2, 'mem.json')));
    const count = manager2.importMemories(exported);
    expect(count).toBe(2);
    expect(manager2.list()).toHaveLength(2);
    rmSync(dir2, { recursive: true, force: true });
  });

  test('remove works', () => {
    const entry = manager.store('Temporary memory')!;
    expect(manager.remove(entry.id)).toBe(true);
    expect(manager.list()).toHaveLength(0);
  });
});
