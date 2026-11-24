"""Integration tests for the self-contained MCP prototype (no real Gmail or network)."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app,TRACE

class LifeAnchorFlow(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Path(self.tmp.name)/"test.sqlite3"
        # bridge intentionally uses a fixed local DB path; reset at each test
        self.client=TestClient(app)
        result=self.client.post("/api/demo/reset")
        self.assertEqual(result.status_code,200,result.text)
        TRACE.clear()
    def tearDown(self):
        self.client.post("/api/demo/reset")
        self.tmp.cleanup()
    def test_refund_lifecycle_and_approval(self):
        r=self.client.post("/api/demo/discover")
        self.assertEqual(r.status_code,200,r.text)
        cid=r.json()["case_id"]
        state=self.client.get("/api/state").json()
        self.assertTrue(any(c["id"]==cid for c in state["cases"]))
        # An unrelated or wrong-amount message must not close the case
        for scenario in ("none","wrong_order","wrong_amount"):
            r=self.client.post("/api/demo/check",json={"case_id":cid,"scenario":scenario})
            self.assertEqual(r.status_code,200,r.text)
            self.assertNotEqual(r.json()["status"],"resolved")
        # A merchant-issued email alone does NOT prove bank receipt
        r=self.client.post("/api/demo/check",json={"case_id":cid,"scenario":"matching_issued"})
        self.assertEqual(r.json()["status"],"awaiting_user_confirmation")
        r=self.client.post("/api/demo/draft",json={"case_id":cid})
        aid=r.json()["action_id"]
        r=self.client.post("/api/demo/review",json={"case_id":cid,"action_id":aid,"decision":"approve"})
        self.assertEqual(r.json()["status"],"approved_not_sent")
        self.assertFalse(r.json()["sent"])
        r=self.client.post("/api/demo/verify",json={"case_id":cid})
        self.assertTrue(r.json()["verified"])
        self.assertEqual(r.json()["status"],"resolved")
        # State persists in SQLite after calls end
        self.assertEqual(self.client.get("/api/state").json()["cases"][0]["status"],"resolved")
    def test_manual_responsibility(self):
        result=self.client.post("/api/cases",json={"title":"Submit internship application","category":"application"})
        self.assertEqual(result.status_code,200,result.text)
        self.assertTrue(result.json()["case_id"].startswith("LA-"))
    def test_invalid_check(self):
        r=self.client.post("/api/demo/discover")
        cid=r.json()["case_id"]
        r=self.client.post("/api/demo/check",json={"case_id":cid,"scenario":"not_a_case"})
        self.assertEqual(r.status_code,400)

if __name__=="__main__":
    unittest.main()
