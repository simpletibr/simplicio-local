"""Test suite for simplicio-local declarative flow and drift prevention.

Enforces criteria of issue #325 (Langflow + Mermaid/imagem contract simplicio.flow/v1):
- Drift test: validates that flow.json references only existing files and lines.
- Completeness: verifies that flow.json, .mmd, .svg/.png and .langflow.json exist.
- Determinism: verifies identical byte output across multiple generator runs.
"""

import json
import unittest
from pathlib import Path

from scripts.generate_flow import (
    FLOW_JSON_PATH,
    FLOW_SCHEMA,
    LANGFLOW_JSON_PATH,
    MMD_PATH,
    PNG_PATH,
    REPO_ROOT,
    SVG_PATH,
    build_langflow_json,
    build_mermaid,
    validate_drift,
)


class TestFlowDrift(unittest.TestCase):
    def setUp(self):
        self.assertTrue(FLOW_JSON_PATH.exists(), f"Missing {FLOW_JSON_PATH}")
        with open(FLOW_JSON_PATH, "r", encoding="utf-8") as f:
            self.flow_data = json.load(f)

    def test_schema_conformance(self):
        self.assertEqual(self.flow_data.get("schema"), FLOW_SCHEMA)
        self.assertIn("inputs", self.flow_data)
        self.assertIn("nodes", self.flow_data)
        self.assertIn("edges", self.flow_data)
        self.assertIn("outputs", self.flow_data)
        self.assertGreater(len(self.flow_data["inputs"]), 0)
        self.assertGreater(len(self.flow_data["nodes"]), 0)
        self.assertGreater(len(self.flow_data["edges"]), 0)
        self.assertGreater(len(self.flow_data["outputs"]), 0)

    def test_no_code_drift(self):
        errors = validate_drift(self.flow_data)
        self.assertEqual(errors, [], "Code drift detected:\n" + "\n".join(errors))

    def test_deterministic_mermaid_generation(self):
        mmd_first = build_mermaid(self.flow_data)
        mmd_second = build_mermaid(self.flow_data)
        self.assertEqual(mmd_first, mmd_second)
        self.assertIn("flowchart TD", mmd_first)
        self.assertIn("subgraph Inputs", mmd_first)
        self.assertIn("subgraph Steps", mmd_first)
        self.assertIn("subgraph Outputs", mmd_first)

    def test_deterministic_langflow_generation(self):
        lf_first = build_langflow_json(self.flow_data)
        lf_second = build_langflow_json(self.flow_data)
        self.assertEqual(
            json.dumps(lf_first, sort_keys=True),
            json.dumps(lf_second, sort_keys=True)
        )
        self.assertIn("data", lf_first)
        self.assertIn("nodes", lf_first["data"])
        self.assertIn("edges", lf_first["data"])
        self.assertGreaterEqual(len(lf_first["data"]["nodes"]), len(self.flow_data["inputs"]) + len(self.flow_data["nodes"]))

    def test_artifacts_exist(self):
        self.assertTrue(FLOW_JSON_PATH.exists())
        self.assertTrue(MMD_PATH.exists())
        self.assertTrue(LANGFLOW_JSON_PATH.exists())
        # At least one rendered image must exist (or both)
        has_image = SVG_PATH.exists() or PNG_PATH.exists()
        self.assertTrue(has_image, "Neither SVG nor PNG was generated")


if __name__ == "__main__":
    unittest.main()
