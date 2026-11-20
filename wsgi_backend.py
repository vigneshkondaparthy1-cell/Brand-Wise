"""Expose the complete BrandWise HTTP API through the deployed WSGI server."""

from email.message import Message
from io import BytesIO

from flask import Flask, Response, request
from flask_talisman import Talisman

import full_backend


full_backend.init_storage()
app = Flask(__name__)
Talisman(
    app,
    content_security_policy={
        "default-src": "'self'",
        "script-src": "'self'",
        "style-src": "'self' 'unsafe-inline'",
        "img-src": "'self' data:",
    },
    force_https=False,
    referrer_policy="strict-origin-when-cross-origin",
)


class RequestHandler(full_backend.Handler):
    """Run the existing HTTP handler against a WSGI request in memory."""

    def __init__(self):
        body = request.get_data()
        self.rfile = BytesIO(body)
        self.wfile = BytesIO()
        self.command = request.method
        self.path = request.full_path.rstrip('?')
        self.request_version = "HTTP/1.1"
        self.requestline = f"{self.command} {self.path} {self.request_version}"
        self.client_address = (request.remote_addr or "127.0.0.1", 0)
        self.close_connection = False
        self.headers = Message()
        for key, value in request.headers.items():
            self.headers[key] = value


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'HEAD', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'HEAD', 'OPTIONS'])
def dispatch(path):
    handler = RequestHandler()
    if request.method == 'POST':
        handler.do_POST()
    elif request.method == 'OPTIONS':
        handler.do_OPTIONS()
    else:
        handler.do_GET()

    raw = handler.wfile.getvalue()
    if b'\r\n\r\n' not in raw:
        return Response('Backend did not return a response.', status=500)
    head, body = raw.split(b'\r\n\r\n', 1)
    lines = head.decode('iso-8859-1').split('\r\n')
    status = int(lines[0].split(' ', 2)[1])
    headers = []
    for line in lines[1:]:
        if ':' in line:
            name, value = line.split(':', 1)
            if name.lower() not in ('connection', 'transfer-encoding', 'content-length'):
                headers.append((name, value.strip()))
    return Response(body if request.method != 'HEAD' else b'', status=status, headers=headers)
