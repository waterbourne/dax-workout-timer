/**
 * LearnQuest Save Lesson Helper
 * 
 * This is a simple Node.js endpoint helper for saving lessons.
 * In production, this would be a server endpoint that writes to the lessons.json file.
 * 
 * For local development, the admin panel uses localStorage.
 * To deploy, set up a simple server endpoint that accepts POST requests
 * and appends lessons to api/lessons.json
 * 
 * Example usage with fetch:
 * 
 * fetch('/api/save-lesson', {
 *   method: 'POST',
 *   headers: { 'Content-Type': 'application/json' },
 *   body: JSON.stringify(lessonData)
 * });
 */

const fs = require('fs');
const path = require('path');

// For Node.js/Express server
function saveLessonEndpoint(req, res) {
    try {
        const lessonData = req.body;
        const lessonsPath = path.join(__dirname, 'lessons.json');
        
        // Read existing lessons
        let data = { lessons: [] };
        if (fs.existsSync(lessonsPath)) {
            const fileContent = fs.readFileSync(lessonsPath, 'utf8');
            data = JSON.parse(fileContent);
        }
        
        // Add new lesson
        data.lessons.push({
            ...lessonData,
            savedAt: new Date().toISOString()
        });
        
        data.lastUpdated = new Date().toISOString();
        
        // Write back
        fs.writeFileSync(lessonsPath, JSON.stringify(data, null, 2));
        
        res.json({ success: true, message: 'Lesson saved successfully' });
    } catch (error) {
        console.error('Error saving lesson:', error);
        res.status(500).json({ success: false, error: error.message });
    }
}

// Simple CLI usage for testing
if (require.main === module) {
    const args = process.argv.slice(2);
    
    if (args[0] === 'export') {
        // Export lessons from localStorage format to JSON
        const lessonsFile = path.join(__dirname, 'lessons.json');
        
        if (fs.existsSync(lessonsFile)) {
            console.log('✅ Lessons file exists at:', lessonsFile);
            const data = JSON.parse(fs.readFileSync(lessonsFile, 'utf8'));
            console.log(`📚 Total lessons: ${data.lessons?.length || 0}`);
            console.log(`🕐 Last updated: ${data.lastUpdated || 'Never'}`);
        } else {
            console.log('Creating new lessons file...');
            fs.writeFileSync(lessonsFile, JSON.stringify({
                version: '1.0',
                lastUpdated: new Date().toISOString(),
                lessons: []
            }, null, 2));
            console.log('✅ Created lessons.json');
        }
    }
    
    if (args[0] === 'backup') {
        const lessonsFile = path.join(__dirname, 'lessons.json');
        const backupFile = path.join(__dirname, `lessons-backup-${Date.now()}.json`);
        
        if (fs.existsSync(lessonsFile)) {
            fs.copyFileSync(lessonsFile, backupFile);
            console.log('✅ Backup created:', backupFile);
        } else {
            console.log('❌ No lessons file to backup');
        }
    }
}

module.exports = { saveLessonEndpoint };