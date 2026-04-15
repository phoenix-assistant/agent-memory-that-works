/**
 * Deduplication via content hash + simple token-based similarity.
 */
import { createHash } from 'crypto';

export function contentHash(text: string): string {
  return createHash('sha256').update(text.trim().toLowerCase()).digest('hex');
}

/** Jaccard similarity on word tokens */
export function similarity(a: string, b: string): number {
  const ta = new Set(tokenize(a));
  const tb = new Set(tokenize(b));
  if (ta.size === 0 && tb.size === 0) return 1;
  let intersection = 0;
  for (const t of ta) if (tb.has(t)) intersection++;
  const union = ta.size + tb.size - intersection;
  return union === 0 ? 1 : intersection / union;
}

function tokenize(text: string): string[] {
  return text.toLowerCase().replace(/[^a-z0-9\s]/g, '').split(/\s+/).filter(Boolean);
}

export function isDuplicate(
  newText: string,
  existing: string[],
  threshold = 0.85
): boolean {
  const hash = contentHash(newText);
  for (const e of existing) {
    if (contentHash(e) === hash) return true;
    if (similarity(newText, e) >= threshold) return true;
  }
  return false;
}
