import http.server
import socketserver
import os
import sys

# python3 serve.py [port]   (default 3000; or set PORT=…)
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get('PORT', 3000))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

handler = http.server.SimpleHTTPRequestHandler
handler.extensions_map.update({'.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript', '.webp': 'image/webp', '.svg': 'image/svg+xml'})

class Quiet(handler):
    def log_message(self, *args):
        pass

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), Quiet) as httpd:
    print(f"Serving at http://localhost:{PORT}")
    httpd.serve_forever()
