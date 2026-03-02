#!/usr/bin/env node
/**
 * Context Cache Compression Agent
 * Archives entries older than 30 days and summarizes them
 */

const fs = require('fs');
const path = require('path');

const CONTEXT_FILE = path.join(__dirname, 'shared', 'context-cache.json');
const ARCHIVE_FILE = path.join(__dirname, 'shared', 'context-archive.json');
const THIRTY_DAYS_MS = 30 * 24 * 60 * 60 * 1000;

function loadJson(filePath) {
    try {
        return JSON.parse(fs.readFileSync(filePath, 'utf8'));
    } catch (e) {
        return {};
    }
}

function saveJson(filePath, data) {
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
}

function isOldEntry(entry) {
    if (!entry.timestamp && !entry.date) return false;
    const entryTime = new Date(entry.timestamp || entry.date).getTime();
    return (Date.now() - entryTime) > THIRTY_DAYS_MS;
}

function summarizeAgentData(agentName, entries) {
    const count = entries.length;
    const themes = [...new Set(entries.map(e => e.theme || e.topic || 'general'))];
    const keyInsights = entries
        .map(e => e.insight || e.keyQuestion || e.contradiction)
        .filter(Boolean)
        .slice(0, 3);
    
    return {
        agent: agentName,
        period: `${entries[0]?.date || 'unknown'} to ${entries[entries.length - 1]?.date || 'unknown'}`,
        totalEntries: count,
        themes: themes.slice(0, 5),
        keyInsights: keyInsights,
        archivedAt: new Date().toISOString()
    };
}

function compressContext() {
    console.log('🔧 Context Cache Compression Starting...\n');
    
    const context = loadJson(CONTEXT_FILE);
    const archive = loadJson(ARCHIVE_FILE);
    
    let totalArchived = 0;
    const summaries = [];
    
    // Process each agent's data
    for (const [agentName, agentData] of Object.entries(context)) {
        if (!agentData || typeof agentData !== 'object') continue;
        
        // Handle different data structures
        let entries = [];
        if (Array.isArray(agentData)) {
            entries = agentData;
        } else if (agentData.recent_7_days) {
            entries = agentData.recent_7_days;
        } else if (agentData.entries) {
            entries = agentData.entries;
        }
        
        const oldEntries = entries.filter(isOldEntry);
        const recentEntries = entries.filter(e => !isOldEntry(e));
        
        if (oldEntries.length > 0) {
            // Create summary
            const summary = summarizeAgentData(agentName, oldEntries);
            summaries.push(summary);
            
            // Add to archive
            if (!archive[agentName]) archive[agentName] = [];
            archive[agentName].push({
                type: 'compressed_archive',
                summary: summary,
                entryCount: oldEntries.length,
                archivedAt: new Date().toISOString(),
                rawEntries: oldEntries // Keep raw data for reference
            });
            
            // Update context with only recent entries
            if (Array.isArray(agentData)) {
                context[agentName] = recentEntries;
            } else if (agentData.recent_7_days) {
                context[agentName].recent_7_days = recentEntries;
            } else if (agentData.entries) {
                context[agentName].entries = recentEntries;
            }
            
            totalArchived += oldEntries.length;
            console.log(`✓ ${agentName}: Archived ${oldEntries.length} entries, kept ${recentEntries.length} recent`);
        }
    }
    
    // Save files
    saveJson(CONTEXT_FILE, context);
    saveJson(ARCHIVE_FILE, archive);
    
    // Create summary report
    const report = {
        runAt: new Date().toISOString(),
        totalEntriesArchived: totalArchived,
        agentsProcessed: summaries.length,
        summaries: summaries
    };
    
    console.log(`\n📊 Compression Complete:`);
    console.log(`   - Total entries archived: ${totalArchived}`);
    console.log(`   - Agents processed: ${summaries.length}`);
    console.log(`   - Context file size reduced`);
    console.log(`   - Archive updated at: ${ARCHIVE_FILE}`);
    
    return report;
}

// Run compression
const report = compressContext();

// Export for cron integration
module.exports = { compressContext, report };
