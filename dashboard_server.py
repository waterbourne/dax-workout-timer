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

PORT = 8080
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
