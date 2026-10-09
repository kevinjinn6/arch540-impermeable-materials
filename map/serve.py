"""
Serve the map folder at http://localhost:8000 (the map, in 2D and 3D).

    cd map
    python3 serve.py

Same as  python3 -m http.server , except that it lets up to 128 browser
requests wait at once instead of 5. The 3D view asks for dozens of ground
tiles together; with the plain server some of them are dropped and the
ground shows flat patches. The published site (GitHub Pages) needs none of this.
"""

import http.server
import os

PORT = 8000            # the address is http://localhost:PORT
WAITING_LIMIT = 128    # requests allowed to queue at once (Python's default is 5)

os.chdir(os.path.dirname(os.path.abspath(__file__)))
http.server.ThreadingHTTPServer.request_queue_size = WAITING_LIMIT
http.server.test(HandlerClass=http.server.SimpleHTTPRequestHandler,
                 ServerClass=http.server.ThreadingHTTPServer, port=PORT, bind="127.0.0.1")
