"""The expanded UI inherits the existing bounded anonymous HTTP envelope."""
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from inventory_intelligence.lab_hosted import HostedLab


class ProductHostedTests(unittest.TestCase):
    def test_product_and_legacy_assets_keep_security_headers(self):
        client = TestClient(HostedLab(burst=100))
        assets = Path(__file__).resolve().parents[1]/'src/inventory_intelligence/product_static'
        paths = ['/', '/lab'] + ['/product-static/'+p.name for p in assets.glob('*')
                               if p.suffix in {'.js', '.css', '.svg'} or p.name == 'THIRD_PARTY_LICENSES.txt']
        self.assertGreater(len(paths), 2)
        for path in paths:
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn("script-src 'self'", response.headers['content-security-policy'])
                self.assertEqual(response.headers['x-content-type-options'], 'nosniff')
        for path in ('/product-static/../product_evidence.json.gz', '/api/product/upload',
                     '/api/product/orders', '/api/product/execute', '/product-static/index.html'):
            self.assertEqual(client.get(path).status_code, 404)

    def test_readiness_does_not_spend_user_allowance(self):
        client = TestClient(HostedLab(burst=1))
        for path in ('/health/live', '/health/ready'):
            response = client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertEqual(client.get('/api/product/overview').status_code, 200)
        self.assertEqual(client.get('/api/product/overview').status_code, 429)
        self.assertEqual(client.get('/health/live').status_code, 200)

    def test_product_read_and_write_method_allowlist(self):
        client = TestClient(HostedLab(burst=100))
        self.assertEqual(client.post('/api/product/overview', json={}).status_code, 405)
        self.assertEqual(client.get('/api/product/scenario').status_code, 405)
        self.assertEqual(client.post('/api/product/scenario', json={}).status_code, 422)
        self.assertEqual(client.post('/api/product/scenarios', json={}).status_code, 422)
        self.assertEqual(client.post('/health/ready', json={}).status_code, 405)
        self.assertEqual(client.put('/lab', json={}).status_code, 405)

if __name__ == '__main__':
    unittest.main()
