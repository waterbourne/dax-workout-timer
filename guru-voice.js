#!/usr/bin/env node
/**
 * Guru Voice Mode - TTS Generator
 * Converts text to audio for podcast delivery
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PODCAST_DIR = path.join(process.env.HOME, 'Music', 'GuruPodcast');
const RSS_FILE = path.join(PODCAST_DIR, 'feed.xml');

// Ensure directory exists
if (!fs.existsSync(PODCAST_DIR)) {
    fs.mkdirSync(PODCAST_DIR, { recursive: true });
}

/**
 * Generate audio from text using macOS say command
 * For better quality, this can be replaced with ElevenLabs API
 */
function generateAudio(text, outputFile) {
    try {
        // macOS built-in TTS (fallback)
        // Using 'Samantha' voice - warm, natural sounding
        const cmd = `say -v Samantha -o "${outputFile}.aiff" "${text.replace(/"/g, '\\"')}"`;
        execSync(cmd, { timeout: 60000 });
        
        // Convert to MP3 using ffmpeg (if available) or keep as aiff
        try {
            const convertCmd = `ffmpeg -i "${outputFile}.aiff" -codec:a libmp3lame -qscale:a 4 "${outputFile}" -y 2>/dev/null`;
            execSync(convertCmd, { timeout: 30000 });
            fs.unlinkSync(`${outputFile}.aiff`); // Clean up aiff
        } catch (e) {
            // ffmpeg not available, keep aiff format
            fs.renameSync(`${outputFile}.aiff`, outputFile.replace('.mp3', '.aiff'));
            return outputFile.replace('.mp3', '.aiff');
        }
        
        return outputFile;
    } catch (error) {
        console.error('TTS generation failed:', error.message);
        return null;
    }
}

/**
 * Generate RSS feed for podcast app
 */
function generateRSSFeed() {
    const files = fs.readdirSync(PODCAST_DIR)
        .filter(f => f.endsWith('.mp3') || f.endsWith('.aiff'))
        .sort().reverse()
        .slice(0, 30); // Keep last 30 episodes
    
    const items = files.map(file => {
        const date = file.match(/(\d{4}-\d{2}-\d{2})/)?.[1] || new Date().toISOString().split('T')[0];
        const stats = fs.statSync(path.join(PODCAST_DIR, file));
        const size = stats.size;
        
        return `
    <item>
      <title>Guru Contemplation - ${date}</title>
      <description>Morning wisdom and contemplation from Guru</description>
      <pubDate>${new Date(date).toUTCString()}</pubDate>
      <enclosure url="file://${path.join(PODCAST_DIR, file)}" length="${size}" type="${file.endsWith('.mp3') ? 'audio/mpeg' : 'audio/aiff'}"/>
      <guid isPermaLink="false">guru-${date}</guid>
    </item>`;
    }).join('\n');
    
    const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" version="2.0">
  <channel>
    <title>Guru - Morning Contemplations</title>
    <description>Daily wisdom and spiritual contemplations for your morning routine</description>
    <language>en</language>
    <link>file://${PODCAST_DIR}</link>
    <itunes:author>Guru</itunes:author>
    <itunes:category text="Religion &amp; Spirituality"/>
    <itunes:explicit>no</itunes:explicit>
${items}
  </channel>
</rss>`;
    
    fs.writeFileSync(RSS_FILE, rss);
    return RSS_FILE;
}

/**
 * Main function - called by Guru cron job
 */
function createGuruPodcast(text) {
    const today = new Date().toISOString().split('T')[0];
    const outputFile = path.join(PODCAST_DIR, `${today}-guru.mp3`);
    
    console.log('🎙️  Generating Guru podcast...');
    console.log(`   Date: ${today}`);
    console.log(`   Output: ${outputFile}`);
    
    // Generate audio
    const audioFile = generateAudio(text, outputFile);
    
    if (audioFile) {
        // Update RSS feed
        const rssPath = generateRSSFeed();
        
        console.log('\n✅ Podcast generated successfully!');
        console.log(`   Audio: ${audioFile}`);
        console.log(`   RSS Feed: ${rssPath}`);
        console.log('\n📱 To subscribe:');
        console.log('   1. Open Apple Podcasts / Overcast / Castro');
        console.log('   2. Add RSS feed: file://' + rssPath);
        
        return {
            audioFile,
            rssPath,
            success: true
        };
    } else {
        console.error('\n❌ Failed to generate podcast');
        return { success: false };
    }
}

// Export for use by agents
module.exports = { createGuruPodcast, generateAudio, generateRSSFeed };

// CLI usage
if (require.main === module) {
    const text = process.argv.slice(2).join(' ') || 'Good morning. Take a moment to breathe deeply and be present.';
    createGuruPodcast(text);
}
