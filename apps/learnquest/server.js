#!/usr/bin/env node
/**
 * LearnQuest API Server
 * Serves static files + API for lessons and progress
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3001;
const LESSONS_FILE = path.join(__dirname, 'api', 'lessons.json');

// MIME types for static files
const MIME_TYPES = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon'
};

// Ensure lessons file exists
if (!fs.existsSync(LESSONS_FILE)) {
  fs.writeFileSync(LESSONS_FILE, JSON.stringify({ version: '1.0', lessons: [] }, null, 2));
}

const server = http.createServer((req, res) => {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  // API endpoint: GET /api/lessons
  if (req.method === 'GET' && req.url === '/api/lessons') {
    const data = JSON.parse(fs.readFileSync(LESSONS_FILE, 'utf8'));
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(data));
    return;
  }

  // API endpoint: POST /api/lessons
  if (req.method === 'POST' && req.url === '/api/lessons') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const newLesson = JSON.parse(body);
        const data = JSON.parse(fs.readFileSync(LESSONS_FILE, 'utf8'));
        
        // Remove existing lesson with same ID
        data.lessons = data.lessons.filter(l => l.id !== newLesson.id);
        
        // Add new lesson at beginning
        data.lessons.unshift(newLesson);
        data.lastUpdated = new Date().toISOString();
        
        fs.writeFileSync(LESSONS_FILE, JSON.stringify(data, null, 2));
        
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, id: newLesson.id }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: e.message }));
      }
    });
    return;
  }

  // Static file serving
  let filePath = req.url === '/' ? '/index.html' : req.url;
  filePath = path.join(__dirname, filePath);
  
  const ext = path.extname(filePath).toLowerCase();
  const contentType = MIME_TYPES[ext] || 'application/octet-stream';
  
  fs.readFile(filePath, (err, content) => {
    if (err) {
      if (err.code === 'ENOENT') {
        // File not found - serve index.html for SPA routes
        fs.readFile(path.join(__dirname, 'index.html'), (err2, indexContent) => {
          if (err2) {
            res.writeHead(404);
            res.end('Not Found');
          } else {
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(indexContent);
          }
        });
      } else {
        res.writeHead(500);
        res.end('Server Error');
      }
    } else {
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content);
    }
  });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`LearnQuest API running on port ${PORT}`);
  console.log(`Access from this device: http://localhost:${PORT}/`);
  console.log(`Access from other devices: http://192.168.68.73:${PORT}/`);
});
