"""
Minimal health check server for Railway deployment.
This starts immediately before the main server to ensure healthcheck passes.
"""
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                "status": "ok",
                "service": "dcisionai-mcp-server",
                "version": "3.2.1",
                "startup": "in_progress"
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def start_health_server(port=8080):
    """Start a minimal health check server"""
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread

