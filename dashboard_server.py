#!/usr/bin/env python3
"""
Simple HTTP server for the OpenClaw Dashboard
Run this to serve the dashboard with live data updates
"""
import http.server
import socketserver
import os
import json
from datetime import datetime, timezone

PORT = 8888
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # Add CORS headers for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()
    
    def do_GET(self):
        # Serve dashboard-data.json with no cache
        if self.path == '/dashboard-data.json':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            
            data_file = os.path.join(DIRECTORY, 'dashboard-data.json')
            if os.path.exists(data_file):
                with open(data_file, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.wfile.write(b'{}')
            return
        
        # Serve HTML files with proper content type
        if self.path.endswith('.html') or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html_file = os.path.join(DIRECTORY, 'dashboard.html')
            if os.path.exists(html_file):
                with open(html_file, 'rb') as f:
                    self.wfile.write(f.read())
            return
        
        # Serve Markdown files
        if self.path.endswith('.md'):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            
            md_file = os.path.join(DIRECTORY, self.path.lstrip('/'))
            if os.path.exists(md_file):
                with open(md_file, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.wfile.write(b'File not found')
            return
        
        super().do_GET()

if __name__ == "__main__":
    os.chdir(DIRECTORY)
    
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"🤖 OpenClaw Dashboard Server")
        print(f"=" * 50)
        print(f"Dashboard running at: http://localhost:{PORT}/dashboard.html")
        print(f"Press Ctrl+C to stop")
        print(f"=" * 50)
        httpd.serve_forever()
