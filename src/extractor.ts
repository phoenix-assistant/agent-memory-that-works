/**
 * Automatic context extraction from conversation text.
 * Pulls out key insights, decisions, patterns, and code references.
 */

export interface ExtractedContext {
  summary: string;
  tags: string[];
  category: 'insight' | 'decision' | 'pattern' | 'code' | 'general';
}

const PATTERN_RULES: Array<{ regex: RegExp; category: ExtractedContext['category']; tag: string }> = [
  { regex: /\b(decided|decision|chose|agreed)\b/i, category: 'decision', tag: 'decision' },
  { regex: /\b(pattern|always|never|convention|rule)\b/i, category: 'pattern', tag: 'pattern' },
  { regex: /\b(function|class|import|export|const|let|var|def |async )\b/, category: 'code', tag: 'code' },
  { regex: /\b(learned|insight|realized|important|key takeaway)\b/i, category: 'insight', tag: 'insight' },
];

export function extractContext(text: string): ExtractedContext {
  const tags: string[] = [];
  let category: ExtractedContext['category'] = 'general';

  for (const rule of PATTERN_RULES) {
    if (rule.regex.test(text)) {
      tags.push(rule.tag);
      if (category === 'general') category = rule.category;
    }
  }

  // Extract potential tags from hashtags or bracketed labels
  const hashTags = text.match(/#(\w+)/g);
  if (hashTags) tags.push(...hashTags.map(t => t.slice(1)));

  const summary = text.length > 200 ? text.slice(0, 197) + '...' : text;

  return { summary, tags: [...new Set(tags)], category };
}
