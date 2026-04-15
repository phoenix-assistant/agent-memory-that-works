/**
 * TF-IDF based relevance retrieval with memory decay.
 */

export interface ScoredResult<T> {
  item: T;
  score: number;
}

function tokenize(text: string): string[] {
  return text.toLowerCase().replace(/[^a-z0-9\s]/g, '').split(/\s+/).filter(Boolean);
}

/** Compute term frequencies for a document */
function tf(tokens: string[]): Map<string, number> {
  const freq = new Map<string, number>();
  for (const t of tokens) freq.set(t, (freq.get(t) || 0) + 1);
  const len = tokens.length || 1;
  for (const [k, v] of freq) freq.set(k, v / len);
  return freq;
}

/** Compute IDF across a corpus */
function idf(corpus: string[][]): Map<string, number> {
  const docCount = corpus.length || 1;
  const df = new Map<string, number>();
  for (const doc of corpus) {
    const seen = new Set(doc);
    for (const t of seen) df.set(t, (df.get(t) || 0) + 1);
  }
  const result = new Map<string, number>();
  for (const [term, count] of df) {
    result.set(term, Math.log(docCount / count));
  }
  return result;
}

/** Score documents against a query using TF-IDF */
export function tfidfScore(query: string, documents: string[]): number[] {
  const queryTokens = tokenize(query);
  const docTokenSets = documents.map(tokenize);
  const idfMap = idf(docTokenSets);

  return docTokenSets.map(docTokens => {
    const tfMap = tf(docTokens);
    let score = 0;
    for (const qt of queryTokens) {
      const termTf = tfMap.get(qt) || 0;
      const termIdf = idfMap.get(qt) || 0;
      score += termTf * termIdf;
    }
    return score;
  });
}

/** Apply exponential decay based on age in days */
export function decayScore(
  baseScore: number,
  ageMs: number,
  halfLifeDays = 30,
  reinforcements = 0
): number {
  const ageDays = ageMs / (1000 * 60 * 60 * 24);
  const boost = 1 + reinforcements * 0.5;
  return baseScore * boost * Math.pow(0.5, ageDays / halfLifeDays);
}

/** Rank items by relevance with decay */
export function rankByRelevance<T>(
  query: string,
  items: Array<{ text: string; createdAt: number; reinforcements?: number; data: T }>
): ScoredResult<T>[] {
  const texts = items.map(i => i.text);
  const scores = tfidfScore(query, texts);
  const now = Date.now();

  return items
    .map((item, i) => ({
      item: item.data,
      score: decayScore(scores[i], now - item.createdAt, 30, item.reinforcements || 0),
    }))
    .filter(r => r.score > 0)
    .sort((a, b) => b.score - a.score);
}
