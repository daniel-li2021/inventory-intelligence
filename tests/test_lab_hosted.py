"""Independent anonymous-hosting boundaries; existing Lab arithmetic is reused."""
import asyncio
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from inventory_intelligence.lab_api import create_app
from inventory_intelligence.lab_hosted import HostedLab


def scope(path='/api/scenarios', method='POST', headers=()):
    return dict(type='http', asgi={'version': '3.0'}, http_version='1.1', method=method,
                scheme='http', path=path, raw_path=path.encode(), query_string=b'',
                headers=list(headers), client=('127.0.0.1', 1), server=('test', 80))


async def exchange(app, events, *, request=None):
    messages=[]
    async def receive():
        if events: return events.pop(0)
        await asyncio.sleep(60)
    async def send(message): messages.append(message)
    await app(request or scope(), receive, send)
    return messages


def status(messages): return next(m['status'] for m in messages if m['type']=='http.response.start')


class HostedLabTests(unittest.TestCase):
    def test_valid_outputs_match_local_app_without_source_calls(self):
        local=TestClient(create_app()); hosted=TestClient(HostedLab())
        with patch('psycopg.connect',side_effect=AssertionError('no database')):
            self.assertEqual(hosted.get('/api/lab').json(),local.get('/api/lab').json())
            self.assertEqual(hosted.get('/api/evidence').json(),local.get('/api/evidence').json())
            for payload in ({},{'demand_percent':125},{'supplier_delay_days':3},
                            {'evidence_case':'incomplete_supply'},{'demand_percent':0}):
                response=hosted.post('/api/scenarios',json=payload)
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.json(),local.post('/api/scenarios',json=payload).json())
            blocked=hosted.post('/api/scenarios',json={'evidence_case':'incomplete_supply'}).json()
            for key in ('plan','simulation','risk','costs'): self.assertIsNone(blocked['scenario'][key])
            self.assertEqual(hosted.get('/api/lab').json()['baseline']['plan']['proposed_order_qty'],12)

    def test_restricted_paths_methods_and_headers(self):
        client=TestClient(HostedLab())
        for path in ('/','/static/lab.css','/static/lab.js','/api/lab','/api/evidence'):
            response=client.get(path)
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.headers['x-content-type-options'],'nosniff')
            self.assertEqual(response.headers['referrer-policy'],'no-referrer')
            self.assertIn("frame-ancestors 'none'",response.headers['content-security-policy'])
            self.assertIn("script-src 'self'",response.headers['content-security-policy'])
            self.assertEqual(response.headers['cache-control'],
                'public, max-age=3600' if path.startswith('/static/') else 'no-store')
        for path in ('/docs','/openapi.json','/redoc','/static/lab_evidence.json','/static/../lab_evidence.json','/api/upload'):
            self.assertEqual(client.get(path).status_code,404)
        self.assertEqual(client.get('/api/scenarios').status_code,405)
        self.assertEqual(client.post('/api/evidence',json={}).status_code,405)
        self.assertEqual(client.put('/',json={}).status_code,405)

    def test_schema_errors_and_bad_evidence_preserve_fail_closed_behavior(self):
        client=TestClient(HostedLab())
        for payload in ({'demand_percent':True},{'moq':0},{'extra':1}):
            self.assertEqual(client.post('/api/scenarios',json=payload).status_code,422)
        bad=TestClient(HostedLab(create_app(evidence={'synthetic':True})))
        for path in ('/api/lab','/api/evidence'): self.assertEqual(bad.get(path).status_code,503)
        self.assertEqual(bad.post('/api/scenarios',json={}).status_code,503)

    def test_global_bucket_refills_without_unbounded_client_identity_storage(self):
        now=[100.0];client=TestClient(HostedLab(clock=lambda:now[0],rate=2,burst=2))
        self.assertEqual(client.get('/api/lab').status_code,200)
        self.assertEqual(client.get('/api/evidence').status_code,200)
        exhausted=client.get('/api/lab');self.assertEqual(exhausted.status_code,429)
        self.assertEqual(exhausted.headers['retry-after'],'1')
        self.assertEqual(client.get('/').status_code,200)
        now[0]+=.5
        self.assertEqual(client.get('/api/lab').status_code,200)
        self.assertEqual(client.get('/api/lab').status_code,429)


class BodyAndConcurrencyTests(unittest.IsolatedAsyncioTestCase):
    async def test_declared_large_body_rejected_before_reading_or_evaluation(self):
        async def forbidden(*args): raise AssertionError('body/application must not be invoked')
        app=HostedLab(forbidden);messages=[]
        await app(scope(headers=[(b'content-length',b'4097')]),forbidden,self.sender(messages))
        self.assertEqual(status(messages),413);self.assertEqual(app.active,0)

    @staticmethod
    def sender(messages):
        async def send(message): messages.append(message)
        return send

    async def test_chunked_actual_size_and_exact_body_boundary(self):
        calls=[]
        async def collector(request,receive,send):
            calls.append((await receive())['body'])
            await send({'type':'http.response.start','status':200,'headers':[]})
            await send({'type':'http.response.body','body':b'ok'})
        app=HostedLab(collector)
        events=[{'type':'http.request','body':b'x'*2048,'more_body':True},
                {'type':'http.request','body':b'y'*2049,'more_body':False}]
        self.assertEqual(status(await exchange(app,events)),413);self.assertEqual(calls,[])
        events=[{'type':'http.request','body':b'x'*2048,'more_body':True},
                {'type':'http.request','body':b'y'*2048,'more_body':False}]
        self.assertEqual(status(await exchange(app,events)),200)
        self.assertEqual(calls,[b'x'*2048+b'y'*2048]);self.assertEqual(app.active,0)

    async def test_malformed_and_disagreeing_lengths_fail_without_application(self):
        async def forbidden(*args): raise AssertionError('application must not be invoked')
        for headers in ([(b'content-length',b'-1')],[(b'content-length',b'invalid')],
                        [(b'content-length',b'2'),(b'content-length',b'2')],[(b'content-length',b'3')]):
            events=[{'type':'http.request','body':b'{}','more_body':False}]
            app=HostedLab(forbidden)
            self.assertEqual(status(await exchange(app,events,request=scope(headers=headers))),400)
            self.assertEqual(app.active,0)

    async def test_slow_body_has_total_deadline_and_releases_capacity(self):
        async def forbidden(*args): raise AssertionError('application must not be invoked')
        app=HostedLab(forbidden,body_seconds=.02)
        messages=await exchange(app,[{'type':'http.request','body':b'{','more_body':True}])
        self.assertEqual(status(messages),408);self.assertEqual(app.active,0)

    async def test_disconnect_and_invalid_event_release_capacity(self):
        async def forbidden(*args): raise AssertionError('application must not be invoked')
        app=HostedLab(forbidden)
        self.assertEqual(await exchange(app,[{'type':'http.disconnect'}]),[])
        self.assertEqual(app.active,0)
        self.assertEqual(status(await exchange(app,[{'type':'unexpected'}])),400)
        self.assertEqual(app.active,0)

    async def test_concurrent_limit_is_immediate_and_recovers_after_completion(self):
        entered=asyncio.Event();release=asyncio.Event()
        async def blocking(request,receive,send):
            entered.set();await release.wait()
            await send({'type':'http.response.start','status':200,'headers':[]})
            await send({'type':'http.response.body','body':b'ok'})
        app=HostedLab(blocking,concurrent=1)
        task=asyncio.create_task(exchange(app,[],request=scope('/api/lab','GET')))
        await entered.wait()
        messages=await exchange(app,[],request=scope('/api/evidence','GET'))
        self.assertEqual(status(messages),503);self.assertEqual(app.active,1)
        release.set();self.assertEqual(status(await task),200);self.assertEqual(app.active,0)
        self.assertEqual(status(await exchange(app,[],request=scope('/api/lab','GET'))),200)

    async def test_exception_and_cancellation_release_admission(self):
        async def failing(*args): raise RuntimeError('injected failure')
        app=HostedLab(failing)
        with self.assertRaises(RuntimeError): await exchange(app,[],request=scope('/api/lab','GET'))
        self.assertEqual(app.active,0)
        entered=asyncio.Event()
        async def wait(*args): entered.set();await asyncio.Event().wait()
        app=HostedLab(wait)
        task=asyncio.create_task(exchange(app,[],request=scope('/api/lab','GET')))
        await entered.wait();task.cancel()
        with self.assertRaises(asyncio.CancelledError): await task
        self.assertEqual(app.active,0)
