import { z } from 'zod';
import { memory_search } from 'openclaw';

/**
 * LCM Memory Search Tool
 * 
 * Unified search across MEMORY.md (curated) and LCM (conversation history).
 */

export const LcmMemorySearchInputSchema = z.object({
  query: z.string().describe('Search query'),
  maxResults: z.number().default(10).describe('Maximum results to return'),
  includeMemory: z.boolean().default(true).describe('Search MEMORY.md'),
  includeLcm: z.boolean().default(true).describe('Search LCM history'),
  dateRange: z.object({
    start: z.string().optional(),
    end: z.string().optional(),
  }).optional().describe('Filter by date range'),
  agents: z.array(z.string()).optional().describe('Filter by agent (Dax, Guru, Sol, etc.)'),
});

export type LcmMemorySearchInput = z.infer<typeof LcmMemorySearchInputSchema>;

export interface LcmMemorySearchOutput {
  results: Array<{
    source: 'memory' | 'lcm' | 'agent-registry';
    content: string;
    timestamp?: string;
    agent?: string;
    path?: string;
    relevanceScore: number;
  }>;
  summary: {
    totalResults: number;
    bySource: Record<string, number>;
    suggestedActions: string[];
  };
}

export async function execute(input: LcmMemorySearchInput): Promise<LcmMemorySearchOutput> {
  const results: LcmMemorySearchOutput['results'] = [];
  
  // 1. Search MEMORY.md (via OpenClaw's memory_search)
  if (input.includeMemory) {
    const memoryResults = await memory_search({ 
      query: input.query,
      maxResults: Math.ceil(input.maxResults / 2),
    });
    
    results.push(...memoryResults.results.map(r => ({
      source: 'memory' as const,
      content: r.content,
      path: r.path,
      relevanceScore: r.score,
    })));
  }
  
  // 2. Search LCM conversation history
  if (input.includeLcm) {
    const db = await getLcmDatabase();
    const lcmResults = await db.searchMessages(input.query, {
      limit: Math.ceil(input.maxResults / 2),
      dateRange: input.dateRange,
      agents: input.agents,
    });
    
    results.push(...lcmResults.map(r => ({
      source: 'lcm' as const,
      content: r.content,
      timestamp: r.timestamp,
      agent: r.agent,
      relevanceScore: r.score,
    })));
  }
  
  // 3. Sort by relevance
  results.sort((a, b) => b.relevanceScore - a.relevanceScore);
  
  // 4. Generate summary
  const bySource = results.reduce((acc, r) => {
    acc[r.source] = (acc[r.source] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  const suggestedActions = generateSuggestions(results, input.query);
  
  return {
    results: results.slice(0, input.maxResults),
    summary: {
      totalResults: results.length,
      bySource,
      suggestedActions,
    },
  };
}

function generateSuggestions(
  results: LcmMemorySearchOutput['results'],
  query: string
): string[] {
  const suggestions: string[] = [];
  
  // Check for agent-specific results
  const agents = new Set(results.filter(r => r.agent).map(r => r.agent));
  if (agents.size > 0) {
    suggestions.push(`Ask ${Array.from(agents).join(', ')} for recent updates`);
  }
  
  // Check for old memory
  const oldResults = results.filter(r => 
    r.timestamp && new Date(r.timestamp) < new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
  );
  if (oldResults.length > 0) {
    suggestions.push('Consider updating MEMORY.md with recent findings');
  }
  
  // Check for gaps
  if (results.length === 0) {
    suggestions.push('No results found — try broadening your search');
  }
  
  return suggestions;
}

async function getLcmDatabase() {
  // Placeholder for LCM database connection
  return {
    searchMessages: async () => [],
  };
}

export const LcmMemorySearchTool = {
  name: 'lcm_memory_search',
  description: 'Unified search across MEMORY.md and LCM conversation history',
  inputSchema: LcmMemorySearchInputSchema,
  execute,
};
