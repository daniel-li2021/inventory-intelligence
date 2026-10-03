"""Strict local HTTP boundary and offline app smoke tests."""
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from inventory_intelligence.lab import load_evidence
from inventory_intelligence.lab_api import create_app


class DecisionLabAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(create_app(evidence=None))

    def test_offline_read_scenario_and_evidence(self):
        baseline = self.client.get("/api/lab")
        self.assertEqual(baseline.status_code, 200)
        self.assertEqual(baseline.json()["baseline"]["plan"]["proposed_order_qty"], 12)
        changed = self.client.post("/api/scenarios", json={"demand_percent": 150})
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(changed.json()["scenario"]["plan"]["proposed_order_qty"], 24)
        self.assertEqual(changed.json()["baseline"], baseline.json()["baseline"])
        evidence = self.client.get("/api/evidence")
        self.assertEqual(evidence.status_code, 200)
        self.assertTrue(evidence.json()["synthetic"])
        self.assertEqual(evidence.json()["business_data"], "synthetic only")

    def test_bounds_and_types_fail_with_422(self):
        bounds = dict(demand_percent=(0, 200), lead_days=(1, 14), review_days=(1, 7),
                      supplier_delay_days=(0, 14), inbound_day=(0, 27),
                      reservation_qty=(0, 100), safety_qty=(0, 100), pack_size=(1, 24),
                      moq=(1, 100), service_target_percent=(0, 100))
        for field, (low, high) in bounds.items():
            for value in (low - 1, high + 1, True, False, float(low), str(low), None, [], {}):
                with self.subTest(field=field, value=value):
                    response = self.client.post("/api/scenarios", json={field: value})
                    self.assertEqual(response.status_code, 422, response.text)
        for value in ("other", 1, True, None):
            with self.subTest(evidence_case=value):
                self.assertEqual(self.client.post("/api/scenarios", json={"evidence_case": value}).status_code, 422)
        for body in ({"extra": 1}, [], 1, "bad"):
            with self.subTest(body=body):
                self.assertEqual(self.client.post("/api/scenarios", json=body).status_code, 422)
        self.assertEqual(self.client.post("/api/scenarios", content="{broken", headers={"content-type": "application/json"}).status_code, 422)

    def test_inclusive_bounds_accept_all_controls(self):
        # Separate requests avoid conflating unrelated boundary effects.
        for field, values in dict(demand_percent=(0, 200), lead_days=(1, 14), review_days=(1, 7),
                                  supplier_delay_days=(0, 14), inbound_day=(0, 27),
                                  reservation_qty=(0, 100), safety_qty=(0, 100), pack_size=(1, 24),
                                  moq=(1, 100), service_target_percent=(0, 100)).items():
            for value in values:
                with self.subTest(field=field, value=value):
                    response = self.client.post("/api/scenarios", json={field: value})
                    self.assertEqual(response.status_code, 200, response.text)
                    self.assertEqual(response.json()["scenario"]["parameters"][field], value)

    def test_incomplete_evidence_is_business_block_not_http_success_values(self):
        response = self.client.post("/api/scenarios", json={"evidence_case": "incomplete_supply"})
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["baseline"]["status"], "assessable")
        self.assertEqual(result["scenario"]["status"], "not_assessable")
        for key in ("plan", "simulation", "costs", "risk"):
            self.assertIsNone(result["scenario"][key])

    def test_invalid_injected_archive_fails_with_503(self):
        client = TestClient(create_app(evidence={"synthetic": True}))
        for method, path in (("get", "/api/lab"), ("get", "/api/evidence"), ("post", "/api/scenarios")):
            with self.subTest(path=path):
                response = getattr(client, method)(path, **({"json": {}} if method == "post" else {}))
                self.assertEqual(response.status_code, 503)
                self.assertNotIn("proposed_order_qty", response.text)

    def test_app_owns_an_immutable_copy_of_injected_evidence(self):
        evidence = load_evidence()
        client = TestClient(create_app(evidence=evidence))
        evidence["future_demand"]["quantities"][0] = 999
        self.assertEqual(client.get("/api/evidence").json()["future_demand"]["quantities"][0], 4)
        self.assertEqual(client.get("/api/lab").status_code, 200)

    def test_app_serves_packaged_assets_without_database_or_model(self):
        with patch("psycopg.connect", side_effect=AssertionError("offline runtime must not connect")):
            client = TestClient(create_app(evidence=None))
            self.assertEqual(client.get("/api/lab").status_code, 200)
            self.assertEqual(client.get("/").status_code, 200)
            html = client.get("/").text
            self.assertIn("Decision", html)
            self.assertNotIn("https://", html)
            self.assertNotIn("http://", html)


if __name__ == "__main__":
    unittest.main()
