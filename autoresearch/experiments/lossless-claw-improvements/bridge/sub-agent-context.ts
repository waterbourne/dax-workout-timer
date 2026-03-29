import { LcmContextEngine } from '../src/engine';
import { SessionKey } from 'openclaw';

/**
 * Sub-Agent Context Inheritance Bridge
 * 
 * Passes parent session's LCM DAG to sub-agents spawned via sessions_spawn.
 */

export interface SubAgentContextConfig {
  inheritLcm: boolean;
  parentSessionKey: SessionKey;
  maxInheritedDepth: number;
  filters?: {
    agents?: string[];
    since?: Date;
    excludeHeartbeat?: boolean;
  };
}

/**
 * Export parent LCM context for sub-agent consumption
 */
export async function exportParentContext(
  parentEngine: LcmContextEngine,
  config: SubAgentContextConfig
): Promise<ExportedContext> {
  const conversationId = parentEngine.getConversationId();
  
  // Get DAG root for this conversation
  const dagRoot = await parentEngine.getDagRoot();
  
  // Apply filters if specified
  let filteredNodes = dagRoot.nodes;
  
  if (config.filters?.excludeHeartbeat !== false) {
    filteredNodes = filteredNodes.filter(n => 
      !n.content.includes('HEARTBEAT_OK') && 
      !n.content.includes('NO_REPLY')
    );
  }
  
  if (config.filters?.agents) {
    filteredNodes = filteredNodes.filter(n => 
      config.filters!.agents!.includes(n.agent || '')
    );
  }
  
  if (config.filters?.since) {
    filteredNodes = filteredNodes.filter(n => 
      new Date(n.timestamp) >= config.filters!.since!
    );
  }
  
  // Limit depth for efficiency
  const prunedDag = pruneDagDepth(dagRoot, config.maxInheritedDepth);
  
  // Serialize for transmission
  const serialized = serializeDag(prunedDag);
  
  return {
    conversationId,
    dag: serialized,
    metadata: {
      exportedAt: new Date().toISOString(),
      nodeCount: filteredNodes.length,
      maxDepth: prunedDag.maxDepth,
      parentSessionKey: config.parentSessionKey,
    },
  };
}

/**
 * Import parent context into sub-agent's LCM instance
 */
export async function importParentContext(
  childEngine: LcmContextEngine,
  exportedContext: ExportedContext
): Promise<void> {
  // Deserialize the DAG
  const dag = deserializeDag(exportedContext.dag);
  
  // Inject into child's LCM as "inherited" context
  await childEngine.injectInheritedContext(dag, {
    sourceConversationId: exportedContext.conversationId,
    inheritedAt: new Date().toISOString(),
  });
  
  // Mark as inherited so queries can distinguish
  childEngine.setContextFlag('inherited_from', exportedContext.metadata.parentSessionKey);
}

/**
 * Bridge function called by sessions_spawn
 */
export async function setupSubAgentLcmContext(
  parentSessionKey: SessionKey,
  childSessionKey: SessionKey,
  options: {
    inheritLcm?: boolean;
    maxDepth?: number;
    agentFilter?: string[];
  } = {}
): Promise<void> {
  if (options.inheritLcm === false) {
    return; // Skip inheritance
  }
  
  // Get parent's LCM engine
  const parentEngine = await LcmContextEngine.forSession(parentSessionKey);
  
  // Export context
  const exported = await exportParentContext(parentEngine, {
    inheritLcm: true,
    parentSessionKey,
    maxInheritedDepth: options.maxDepth || 3,
    filters: {
      agents: options.agentFilter,
      excludeHeartbeat: true,
    },
  });
  
  // Store in temp location for child to pick up
  await storeExportedContext(childSessionKey, exported);
}

/**
 * Called by sub-agent on startup
 */
export async function initializeSubAgentLcmContext(
  childSessionKey: SessionKey
): Promise<boolean> {
  // Check for inherited context
  const exported = await retrieveExportedContext(childSessionKey);
  
  if (!exported) {
    return false; // No inheritance
  }
  
  // Get or create child's LCM engine
  const childEngine = await LcmContextEngine.forSession(childSessionKey);
  
  // Import the context
  await importParentContext(childEngine, exported);
  
  // Clean up temp storage
  await clearExportedContext(childSessionKey);
  
  return true;
}

// Helper types and functions

interface ExportedContext {
  conversationId: string;
  dag: string; // Serialized
  metadata: {
    exportedAt: string;
    nodeCount: number;
    maxDepth: number;
    parentSessionKey: SessionKey;
  };
}

function pruneDagDepth(dag: Dag, maxDepth: number): Dag {
  // Implementation: traverse DAG and prune nodes beyond maxDepth
  return dag;
}

function serializeDag(dag: Dag): string {
  // Implementation: compress and serialize
  return JSON.stringify(dag);
}

function deserializeDag(serialized: string): Dag {
  return JSON.parse(serialized);
}

async function storeExportedContext(
  childSessionKey: SessionKey,
  context: ExportedContext
): Promise<void> {
  // Store in shared temp location
  const store = await getSharedStore();
  await store.set(`lcm-inherit:${childSessionKey}`, context, { ttl: 3600 });
}

async function retrieveExportedContext(
  childSessionKey: SessionKey
): Promise<ExportedContext | null> {
  const store = await getSharedStore();
  return store.get(`lcm-inherit:${childSessionKey}`);
}

async function clearExportedContext(childSessionKey: SessionKey): Promise<void> {
  const store = await getSharedStore();
  await store.delete(`lcm-inherit:${childSessionKey}`);
}

async function getSharedStore() {
  // Returns shared key-value store (Redis, SQLite, etc.)
  // Placeholder implementation
  return {
    set: async () => {},
    get: async () => null,
    delete: async () => {},
  };
}

interface Dag {
  nodes: Array<{
    id: string;
    content: string;
    timestamp: string;
    agent?: string;
    children: string[];
  }>;
  maxDepth: number;
}
