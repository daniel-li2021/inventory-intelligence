"""Bounded anonymous serving wrapper for the unchanged synthetic Decision Lab.

One worker owns one global bucket; this limits admitted API work, not network DoS.
"""
import asyncio
import json
import time

from .lab_api import create_app

API_PATHS = {'/api/lab', '/api/evidence', '/api/lab/evidence'}
ASSETS = {'/', '/static/lab.css', '/static/lab.js'}
HEADERS = [(b'x-content-type-options', b'nosniff'),
           (b'referrer-policy', b'no-referrer'),
           (b'permissions-policy', b'camera=(), microphone=(), geolocation=()'),
           (b'content-security-policy', b"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")]


class HostedLab:
    def __init__(self, application=None, *, clock=time.monotonic, rate=2, burst=20,
                 concurrent=4, body_limit=4096, body_seconds=5):
        self.application = application if application is not None else create_app()
        self.clock, self.rate, self.burst = clock, rate, burst
        self.tokens, self.last, self.active = float(burst), clock(), 0
        self.concurrent, self.body_limit, self.body_seconds = concurrent, body_limit, body_seconds

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'lifespan':
            return await self.application(scope, receive, send)
        if scope['type'] != 'http':
            if scope['type'] == 'websocket': await send({'type': 'websocket.close', 'code': 1008})
            return
        path, method = scope['path'], scope['method']

        async def secured(message):
            if message['type'] == 'http.response.start':
                cache = b'public, max-age=3600' if path in ASSETS and path != '/' else b'no-store'
                message = {**message, 'headers': [*message.get('headers', []), *HEADERS, (b'cache-control', cache)]}
            await send(message)

        async def reject(status, detail, *, retry=False):
            headers = [(b'content-type', b'application/json')]
            if retry: headers.append((b'retry-after', b'1'))
            await secured({'type': 'http.response.start', 'status': status, 'headers': headers})
            await secured({'type': 'http.response.body', 'body': json.dumps({'detail': detail}).encode()})

        api = path in API_PATHS or path == '/api/scenarios'
        if path not in API_PATHS | ASSETS | {'/api/scenarios'}:
            return await reject(404, 'Not found')
        expected = 'POST' if path == '/api/scenarios' else 'GET'
        if method != expected:
            return await reject(405, 'Method not allowed')
        if not api: return await self.application(scope, receive, secured)

        # No await between admission checks and acquisition: one event loop/worker.
        now = self.clock()
        self.tokens = min(self.burst, self.tokens + max(0, now - self.last) * self.rate)
        self.last = now
        if self.active >= self.concurrent:
            return await reject(503, 'Demo is busy; retry shortly', retry=True)
        if self.tokens < 1:
            return await reject(429, 'Demo request allowance exhausted; retry shortly', retry=True)
        self.tokens -= 1
        self.active += 1
        try:
            if method == 'POST':
                lengths = [v for k, v in scope.get('headers', []) if k.lower() == b'content-length']
                if lengths:
                    try:
                        if len(lengths) != 1 or not lengths[0].isdigit(): raise ValueError()
                        declared = int(lengths[0])
                    except ValueError: return await reject(400, 'Invalid content length')
                    if declared > self.body_limit: return await reject(413, 'Scenario body exceeds 4096 bytes')
                body = bytearray()
                deadline = asyncio.get_running_loop().time() + self.body_seconds
                while True:
                    remaining = deadline - asyncio.get_running_loop().time()
                    if remaining <= 0: return await reject(408, 'Scenario body read timed out')
                    try: message = await asyncio.wait_for(receive(), remaining)
                    except TimeoutError: return await reject(408, 'Scenario body read timed out')
                    if message['type'] == 'http.disconnect': return
                    if message['type'] != 'http.request': return await reject(400, 'Invalid request body event')
                    chunk = message.get('body', b'')
                    if len(body) + len(chunk) > self.body_limit: return await reject(413, 'Scenario body exceeds 4096 bytes')
                    body.extend(chunk)
                    if not message.get('more_body', False): break
                if lengths and len(body) != declared: return await reject(400, 'Content length disagrees with body')
                delivered = False
                async def buffered():
                    nonlocal delivered
                    if not delivered:
                        delivered = True
                        return {'type': 'http.request', 'body': bytes(body), 'more_body': False}
                    return await receive()
                await self.application(scope, buffered, secured)
            else:
                await self.application(scope, receive, secured)
        finally:
            self.active -= 1


app = HostedLab()
