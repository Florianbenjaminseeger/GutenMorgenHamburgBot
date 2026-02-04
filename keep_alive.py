from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import os

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active and running!")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    print(f"Web server started on port {port}")
    server.serve_forever()

def start_keep_alive():
    t = Thread(target=run_server, daemon=True)
    t.start()
