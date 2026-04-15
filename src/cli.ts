#!/usr/bin/env node
import { resolve, join } from 'path';
import { existsSync, writeFileSync, readFileSync } from 'fs';
import { MemoryManager } from './memory';
import { FileBackend } from './backends/file';

const args = process.argv.slice(2);
const cmd = args[0];

const memDir = process.env.AGENT_MEM_DIR || join(process.cwd(), '.agent-memory');
const memFile = join(memDir, 'memories.json');
const backend = new FileBackend(memFile);
const manager = new MemoryManager(backend);

function usage(): void {
  console.log(`agent-mem — practical persistent memory for AI coding agents

Commands:
  store <text>           Store a memory (auto-extracts context, deduplicates)
  recall <query>         Recall relevant memories (TF-IDF + decay scored)
  list                   List all memories
  remove <id>            Remove a memory by ID
  reinforce <id>         Reinforce a memory (boost its relevance)
  clear                  Clear all memories
  export [file]          Export memories to JSON
  import <file>          Import memories from JSON
  stats                  Show memory stats`);
}

switch (cmd) {
  case 'store': {
    const text = args.slice(1).join(' ');
    if (!text) { console.error('Usage: agent-mem store <text>'); process.exit(1); }
    const entry = manager.store(text);
    if (entry) {
      console.log(`Stored: ${entry.id.slice(0, 8)} [${entry.category}] ${entry.summary}`);
    } else {
      console.log('Duplicate detected — existing memory reinforced.');
    }
    break;
  }
  case 'recall': {
    const query = args.slice(1).join(' ');
    if (!query) { console.error('Usage: agent-mem recall <query>'); process.exit(1); }
    const results = manager.recall(query);
    if (results.length === 0) { console.log('No relevant memories found.'); break; }
    for (const r of results) {
      const e = r.item;
      console.log(`[${r.score.toFixed(3)}] ${e.id.slice(0, 8)} | ${e.category} | ${e.summary}`);
    }
    break;
  }
  case 'list': {
    const all = manager.list();
    if (all.length === 0) { console.log('No memories stored.'); break; }
    for (const e of all) {
      console.log(`${e.id.slice(0, 8)} | ${e.category.padEnd(10)} | r:${e.reinforcements} | ${e.summary}`);
    }
    console.log(`\nTotal: ${all.length} memories`);
    break;
  }
  case 'remove': {
    const id = args[1];
    if (!id) { console.error('Usage: agent-mem remove <id>'); process.exit(1); }
    // Support partial IDs
    const all = manager.list();
    const match = all.find(e => e.id.startsWith(id));
    if (match && manager.remove(match.id)) console.log(`Removed ${match.id.slice(0, 8)}`);
    else console.error('Memory not found.');
    break;
  }
  case 'reinforce': {
    const id = args[1];
    if (!id) { console.error('Usage: agent-mem reinforce <id>'); process.exit(1); }
    manager.reinforce(id);
    console.log('Reinforced.');
    break;
  }
  case 'clear':
    manager.clear();
    console.log('All memories cleared.');
    break;
  case 'export': {
    const data = manager.exportMemories();
    const outFile = args[1];
    if (outFile) { writeFileSync(outFile, data); console.log(`Exported to ${outFile}`); }
    else console.log(data);
    break;
  }
  case 'import': {
    const file = args[1];
    if (!file || !existsSync(file)) { console.error('Usage: agent-mem import <file>'); process.exit(1); }
    const count = manager.importMemories(readFileSync(file, 'utf-8'));
    console.log(`Imported ${count} memories.`);
    break;
  }
  case 'stats': {
    const all = manager.list();
    const cats = new Map<string, number>();
    for (const e of all) cats.set(e.category, (cats.get(e.category) || 0) + 1);
    console.log(`Total memories: ${all.length}`);
    for (const [c, n] of cats) console.log(`  ${c}: ${n}`);
    break;
  }
  default:
    usage();
    if (cmd) process.exit(1);
}
