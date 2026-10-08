#!/usr/bin/env python3
"""Deterministic flow generator and drift checker for simplicio-local.

Implements contract `simplicio.flow/v1` (simplicio-mapper#657 / simplicio-local#325):
- Reads/maintains `docs/flow/simplicio-local.flow.json` (source of truth).
- Validates drift: every referenced source file and symbol line must exist.
- Compiles `docs/flow/simplicio-local.mmd` (Mermaid flowchart).
- Renders `docs/flow/simplicio-local.svg` and `docs/flow/simplicio-local.png` via mmdc.
- Emits `docs/flow/langflow/simplicio-local.langflow.json` (importable in Langflow 1.12).
- Emits helper components for Langflow custom nodes.
- Optionally pushes to Langflow (`--push-langflow http://localhost:7860`).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

FLOW_SCHEMA = "simplicio.flow/v1"
REPO_ROOT = Path(__file__).resolve().parent.parent
FLOW_DIR = REPO_ROOT / "docs" / "flow"
FLOW_JSON_PATH = FLOW_DIR / "simplicio-local.flow.json"
MMD_PATH = FLOW_DIR / "simplicio-local.mmd"
SVG_PATH = FLOW_DIR / "simplicio-local.svg"
PNG_PATH = FLOW_DIR / "simplicio-local.png"
LANGFLOW_DIR = FLOW_DIR / "langflow"
LANGFLOW_JSON_PATH = LANGFLOW_DIR / "simplicio-local.langflow.json"
COMPONENTS_DIR = LANGFLOW_DIR / "components"


def get_default_flow_data() -> dict[str, Any]:
    return {
        "$schema": FLOW_SCHEMA,
        "schema": FLOW_SCHEMA,
        "name": "simplicio-local",
        "version": "0.1.53",
        "description": "Fluxo declarativo end-to-end do simplicio-local: entrada -> passos -> saídas",
        "inputs": [
            {
                "id": "in_mapper_cli",
                "label": "CLI: llm-project-mapper (Scaffolding & Templates)",
                "kind": "input",
                "source": {
                    "file": "bin/cli.js",
                    "line": 411,
                    "symbol": "printHelp"
                }
            },
            {
                "id": "in_us4_cli",
                "label": "CLI: us4-cli (Runtime & Tools Wrapper)",
                "kind": "input",
                "source": {
                    "file": "bin/us4-cli.js",
                    "line": 101,
                    "symbol": "printHelp"
                }
            },
            {
                "id": "in_openai_http",
                "label": "HTTP: OpenAI Server API (/v1/chat/completions, /v1/embeddings)",
                "kind": "input",
                "source": {
                    "file": "scripts/openai_serve.py",
                    "line": 437,
                    "symbol": "do_POST"
                }
            },
            {
                "id": "in_health_http",
                "label": "HTTP: Health & Models API (/health, /v1/models)",
                "kind": "input",
                "source": {
                    "file": "scripts/openai_serve.py",
                    "line": 409,
                    "symbol": "do_GET"
                }
            },
            {
                "id": "in_model_weights",
                "label": "File: Safetensors / GGUF Model Weights",
                "kind": "input",
                "source": {
                    "file": "local_data_plane/model_resolver.py",
                    "line": 154,
                    "symbol": "resolve_model"
                }
            }
        ],
        "nodes": [
            {
                "id": "step_admission",
                "label": "Runtime Admission & Policy Lease Gate",
                "kind": "step",
                "source": {
                    "file": "bin/us4-cli.js",
                    "line": 13,
                    "symbol": "hasRuntimeAdmission"
                }
            },
            {
                "id": "step_probe_topology",
                "label": "Hardware Topology & ISA Detection (AVX2, NEON, AMX, ANE)",
                "kind": "step",
                "source": {
                    "file": "local_data_plane/hardware_topology.py",
                    "line": 96,
                    "symbol": "detect_hardware_topology"
                }
            },
            {
                "id": "step_scaffold_detect",
                "label": "Scaffolding Stack Detection & Template Copy",
                "kind": "step",
                "source": {
                    "file": "bin/cli.js",
                    "line": 501,
                    "symbol": "detectStack"
                }
            },
            {
                "id": "step_doctor_diag",
                "label": "Host Doctor & Hardware Diagnostics",
                "kind": "step",
                "source": {
                    "file": "engine/c/doctor.py",
                    "line": 186,
                    "symbol": "main"
                }
            },
            {
                "id": "step_resource_plan",
                "label": "Resource Planner & RSS Ceiling Check",
                "kind": "step",
                "source": {
                    "file": "engine/c/resource_plan.py",
                    "line": 108,
                    "symbol": "build_plan"
                }
            },
            {
                "id": "step_model_verify",
                "label": "Model Resolver & Artifact Verification",
                "kind": "step",
                "source": {
                    "file": "local_data_plane/model_resolver.py",
                    "line": 100,
                    "symbol": "ModelResolver"
                }
            },
            {
                "id": "step_layout_packing",
                "label": "Weight Packing & Cache-Aware Tiling",
                "kind": "step",
                "source": {
                    "file": "local_data_plane/layout_packing.py",
                    "line": 121,
                    "symbol": "pack_int8_rhs"
                }
            },
            {
                "id": "step_batching",
                "label": "Isolated Continuous Batching & KV Management",
                "kind": "step",
                "source": {
                    "file": "local_data_plane/layout_packing.py",
                    "line": 260,
                    "symbol": "form_isolated_batch"
                }
            },
            {
                "id": "step_autotuner",
                "label": "Bounded Autotuner & Physical Kernel Selector",
                "kind": "step",
                "source": {
                    "file": "local_data_plane/kernel_dispatch.py",
                    "line": 142,
                    "symbol": "run_bounded_autotune"
                }
            },
            {
                "id": "step_inference_exec",
                "label": "Engine Inference Execution (C Engine / MLX / Metal)",
                "kind": "step",
                "source": {
                    "file": "scripts/openai_serve.py",
                    "line": 296,
                    "symbol": "_proxy_upstream"
                }
            },
            {
                "id": "step_embeddings_exec",
                "label": "In-Process Embeddings Generation",
                "kind": "step",
                "source": {
                    "file": "scripts/openai_serve.py",
                    "line": 358,
                    "symbol": "_handle_embeddings"
                }
            },
            {
                "id": "step_simd_gates",
                "label": "SIMD Correctness & Differential Release Gate",
                "kind": "step",
                "source": {
                    "file": "local_data_plane/simd_validation.py",
                    "line": 102,
                    "symbol": "evaluate_release_gate"
                }
            },
            {
                "id": "step_telemetry",
                "label": "Telemetry Collection & Immutable Receipt Builder",
                "kind": "step",
                "source": {
                    "file": "local_data_plane/telemetry.py",
                    "line": 71,
                    "symbol": "ReceiptBuilder"
                }
            },
            {
                "id": "store_model_cache",
                "label": "Packed Weights & Model Cache Directory",
                "kind": "store",
                "source": {
                    "file": "local_data_plane/layout_packing.py",
                    "line": 146,
                    "symbol": "AtomicPackedCache"
                }
            },
            {
                "id": "store_tuning_cache",
                "label": "Hardware-Tuning Persistent Key Cache",
                "kind": "store",
                "source": {
                    "file": "local_data_plane/kernel_dispatch.py",
                    "line": 81,
                    "symbol": "PersistentTuningCache"
                }
            }
        ],
        "edges": [
            {
                "from": "in_mapper_cli",
                "to": "step_scaffold_detect",
                "label": "scaffold flags",
                "evidence": "bin/cli.js:450"
            },
            {
                "from": "step_scaffold_detect",
                "to": "out_scaffold_files",
                "label": "emit files",
                "evidence": "bin/cli.js:640"
            },
            {
                "from": "in_us4_cli",
                "to": "step_admission",
                "label": "command dispatch",
                "evidence": "bin/us4-cli.js:20"
            },
            {
                "from": "step_admission",
                "to": "step_probe_topology",
                "label": "probe",
                "evidence": "bin/us4-cli.js:254"
            },
            {
                "from": "step_admission",
                "to": "step_doctor_diag",
                "label": "doctor",
                "evidence": "bin/us4-cli.js:239"
            },
            {
                "from": "step_admission",
                "to": "step_resource_plan",
                "label": "plan",
                "evidence": "bin/us4-cli.js:242"
            },
            {
                "from": "step_probe_topology",
                "to": "out_cli_report",
                "label": "print hardware",
                "evidence": "bin/cli.js:355"
            },
            {
                "from": "step_doctor_diag",
                "to": "out_cli_report",
                "label": "print diagnostics",
                "evidence": "engine/c/doctor.py:186"
            },
            {
                "from": "step_resource_plan",
                "to": "out_cli_report",
                "label": "print plan",
                "evidence": "engine/c/resource_plan.py:250"
            },
            {
                "from": "in_openai_http",
                "to": "step_admission",
                "label": "POST /v1/*",
                "evidence": "scripts/openai_serve.py:437"
            },
            {
                "from": "in_health_http",
                "to": "out_openai_resp",
                "label": "GET /health",
                "evidence": "scripts/openai_serve.py:410"
            },
            {
                "from": "step_admission",
                "to": "step_model_verify",
                "label": "verify lease",
                "evidence": "scripts/openai_serve.py:120"
            },
            {
                "from": "in_model_weights",
                "to": "step_model_verify",
                "label": "weights path",
                "evidence": "local_data_plane/model_resolver.py:154"
            },
            {
                "from": "step_model_verify",
                "to": "step_layout_packing",
                "label": "quant tensors",
                "evidence": "local_data_plane/layout_packing.py:121"
            },
            {
                "from": "step_layout_packing",
                "to": "store_model_cache",
                "label": "cache packed",
                "evidence": "local_data_plane/layout_packing.py:150"
            },
            {
                "from": "step_layout_packing",
                "to": "step_batching",
                "label": "packed tiles",
                "evidence": "local_data_plane/layout_packing.py:207"
            },
            {
                "from": "step_probe_topology",
                "to": "step_autotuner",
                "label": "detected ISA",
                "evidence": "local_data_plane/hardware_topology.py:96"
            },
            {
                "from": "store_tuning_cache",
                "to": "step_autotuner",
                "label": "read key",
                "evidence": "local_data_plane/kernel_dispatch.py:90"
            },
            {
                "from": "step_autotuner",
                "to": "step_inference_exec",
                "label": "selected kernel",
                "evidence": "local_data_plane/kernel_dispatch.py:186"
            },
            {
                "from": "step_batching",
                "to": "step_inference_exec",
                "label": "batch queue",
                "evidence": "local_data_plane/layout_packing.py:260"
            },
            {
                "from": "step_admission",
                "to": "step_embeddings_exec",
                "label": "embed text",
                "evidence": "scripts/openai_serve.py:358"
            },
            {
                "from": "step_embeddings_exec",
                "to": "out_embeddings",
                "label": "vectors",
                "evidence": "scripts/openai_serve.py:390"
            },
            {
                "from": "step_inference_exec",
                "to": "step_simd_gates",
                "label": "output logits",
                "evidence": "local_data_plane/simd_validation.py:59"
            },
            {
                "from": "step_simd_gates",
                "to": "step_telemetry",
                "label": "gate outcome",
                "evidence": "local_data_plane/simd_validation.py:133"
            },
            {
                "from": "step_telemetry",
                "to": "out_receipts",
                "label": "emit receipt",
                "evidence": "local_data_plane/telemetry.py:71"
            },
            {
                "from": "step_inference_exec",
                "to": "out_openai_resp",
                "label": "stream tokens",
                "evidence": "scripts/openai_serve.py:328"
            }
        ],
        "outputs": [
            {
                "id": "out_scaffold_files",
                "label": "Scaffolded Project Specs & Starter Files",
                "kind": "output",
                "source": {
                    "file": "bin/cli.js",
                    "line": 606,
                    "symbol": "copyTemplate"
                }
            },
            {
                "id": "out_cli_report",
                "label": "CLI Terminal Output & Diagnostics Report",
                "kind": "output",
                "source": {
                    "file": "bin/us4-cli.js",
                    "line": 192,
                    "symbol": "runNative"
                }
            },
            {
                "id": "out_openai_resp",
                "label": "OpenAI API JSON & SSE Streaming Tokens",
                "kind": "output",
                "source": {
                    "file": "scripts/openai_serve.py",
                    "line": 296,
                    "symbol": "_proxy_upstream"
                }
            },
            {
                "id": "out_embeddings",
                "label": "Embedding Vectors JSON Response",
                "kind": "output",
                "source": {
                    "file": "scripts/openai_serve.py",
                    "line": 358,
                    "symbol": "_handle_embeddings"
                }
            },
            {
                "id": "out_receipts",
                "label": "SIMD Release Receipts & Tuning Cache",
                "kind": "output",
                "source": {
                    "file": "local_data_plane/simd_validation.py",
                    "line": 133,
                    "symbol": "build_simd_receipt"
                }
            }
        ],
        "generation": {
            "generator": "scripts/generate_flow.py",
            "contract": FLOW_SCHEMA,
            "deterministic": True
        }
    }


def validate_drift(data: dict[str, Any]) -> list[str]:
    """Verify that all files and commands referenced in flow.json exist."""
    errors: list[str] = []
    all_elements = data.get("inputs", []) + data.get("nodes", []) + data.get("outputs", [])
    
    for elem in all_elements:
        elem_id = elem.get("id", "unknown")
        src = elem.get("source", {})
        file_rel = src.get("file")
        if not file_rel:
            errors.append(f"Node {elem_id}: missing 'source.file'")
            continue
        full_path = REPO_ROOT / file_rel
        if not full_path.exists():
            errors.append(f"Drift detected in {elem_id}: file '{file_rel}' does not exist on disk")
            continue
        line_num = src.get("line")
        symbol = src.get("symbol")
        if line_num and isinstance(line_num, int) and line_num > 0:
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                if line_num > len(lines):
                    errors.append(f"Drift in {elem_id}: line {line_num} exceeds {len(lines)} lines of {file_rel}")
                elif symbol:
                    window = lines[max(0, line_num - 15):min(len(lines), line_num + 15)]
                    if not any(symbol in l for l in window):
                        errors.append(f"Drift in {elem_id}: symbol '{symbol}' not found near line {line_num} in {file_rel}")
            except Exception as e:
                errors.append(f"Could not read {file_rel}: {e}")

    for edge in data.get("edges", []):
        evidence = edge.get("evidence", "")
        if ":" in evidence:
            f_rel, _ = evidence.split(":", 1)
            if not (REPO_ROOT / f_rel).exists():
                errors.append(f"Edge {edge.get('from')}->{edge.get('to')}: evidence file '{f_rel}' not found")

    return errors


def build_mermaid(data: dict[str, Any]) -> str:
    """Build deterministic Mermaid flowchart TD representation."""
    lines: list[str] = [
        "%% Auto-generated deterministic Mermaid flow for simplicio-local (simplicio.flow/v1)",
        "flowchart TD",
        "    classDef inputStyle fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0369a1;",
        "    classDef stepStyle fill:#f8fafc,stroke:#64748b,stroke-width:1.5px,color:#0f172a;",
        "    classDef storeStyle fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#92400e;",
        "    classDef outputStyle fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#15803d;",
        "",
        "    subgraph Inputs [\"Entradas\"]"
    ]

    for inp in sorted(data.get("inputs", []), key=lambda x: x["id"]):
        label = inp["label"].replace('"', "'")
        lines.append(f"        {inp['id']}[\"{label}\"]:::inputStyle")
    lines.append("    end")
    lines.append("")

    lines.append("    subgraph Steps [\"Processamento e Aceleração SIMD\"]")
    step_nodes = [n for n in data.get("nodes", []) if n.get("kind") == "step"]
    for step in sorted(step_nodes, key=lambda x: x["id"]):
        label = step["label"].replace('"', "'")
        lines.append(f"        {step['id']}[\"{label}\"]:::stepStyle")
    lines.append("    end")
    lines.append("")

    store_nodes = [n for n in data.get("nodes", []) if n.get("kind") == "store"]
    if store_nodes:
        lines.append("    subgraph Stores [\"Armazenamento e Cache\"]")
        for store in sorted(store_nodes, key=lambda x: x["id"]):
            label = store["label"].replace('"', "'")
            lines.append(f"        {store['id']}[(\"{label}\")]:::storeStyle")
        lines.append("    end")
        lines.append("")

    lines.append("    subgraph Outputs [\"Saídas\"]")
    for out in sorted(data.get("outputs", []), key=lambda x: x["id"]):
        label = out["label"].replace('"', "'")
        lines.append(f"        {out['id']}[\"{label}\"]:::outputStyle")
    lines.append("    end")
    lines.append("")

    lines.append("    %% Conexões determinísticas")
    edges = sorted(data.get("edges", []), key=lambda e: (e["from"], e["to"]))
    for edge in edges:
        lbl = edge.get("label", "").replace('"', "'")
        if lbl:
            lines.append(f"    {edge['from']} -->|\"{lbl}\"| {edge['to']}")
        else:
            lines.append(f"    {edge['from']} --> {edge['to']}")

    return "\n".join(lines) + "\n"


def build_langflow_json(data: dict[str, Any]) -> dict[str, Any]:
    """Generate a Langflow 1.12.0 compatible flow definition."""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    columns: dict[str, int] = {
        "input": 50,
        "step": 450,
        "store": 850,
        "output": 1250
    }
    y_offsets: dict[str, int] = {
        "input": 50,
        "step": 50,
        "store": 50,
        "output": 50
    }

    all_nodes = data.get("inputs", []) + data.get("nodes", []) + data.get("outputs", [])
    for node in sorted(all_nodes, key=lambda x: x["id"]):
        kind = node.get("kind", "step")
        x = columns.get(kind, 450)
        y = y_offsets.get(kind, 50)
        y_offsets[kind] = y + 140

        nodes.append({
            "id": node["id"],
            "type": "genericNode",
            "position": {"x": x, "y": y},
            "data": {
                "type": "CustomComponent",
                "id": node["id"],
                "node": {
                    "display_name": node["label"],
                    "description": f"Source: {node.get('source', {}).get('file', '')}:{node.get('source', {}).get('line', '')}",
                    "template": {
                        "kind": {"type": "str", "value": kind},
                        "file": {"type": "str", "value": node.get("source", {}).get("file", "")},
                        "line": {"type": "int", "value": node.get("source", {}).get("line", 0)},
                        "symbol": {"type": "str", "value": node.get("source", {}).get("symbol", "")}
                    }
                }
            }
        })

    for idx, edge in enumerate(sorted(data.get("edges", []), key=lambda e: (e["from"], e["to"]))):
        edges.append({
            "id": f"edge_{idx}_{edge['from']}_{edge['to']}",
            "source": edge["from"],
            "target": edge["to"],
            "data": {
                "label": edge.get("label", ""),
                "evidence": edge.get("evidence", "")
            }
        })

    return {
        "name": "simplicio-local",
        "description": data.get("description", "Simplicio Local Flow"),
        "data": {
            "nodes": nodes,
            "edges": edges,
            "viewport": {"x": 0, "y": 0, "zoom": 0.8}
        }
    }


def emit_langflow_components() -> None:
    """Emit the custom python components for Langflow import."""
    COMPONENTS_DIR.mkdir(parents=True, exist_ok=True)
    
    flow_node_code = '''"""Simplicio Flow Node custom component for Langflow 1.12."""
from typing import Optional
try:
    from langflow.custom import Component
    from langflow.io import Output, StrInput, IntInput
    from langflow.schema import Data
except ImportError:
    class Component: pass
    Output = StrInput = IntInput = Data = object

class SimplicioFlowNode(Component):
    display_name = "Simplicio Flow Node"
    description = "Represents an Input, Step, Store, or Output node from simplicio.flow/v1"
    icon = "workflow"

    inputs = [
        StrInput(name="node_id", display_name="Node ID", value=""),
        StrInput(name="kind", display_name="Kind (input|step|store|output)", value="step"),
        StrInput(name="source_file", display_name="Source File", value=""),
        IntInput(name="source_line", display_name="Source Line", value=0),
        StrInput(name="source_symbol", display_name="Source Symbol", value=""),
    ]

    outputs = [
        Output(display_name="Node Data", name="data", method="build_data"),
    ]

    def build_data(self) -> Data:
        return Data(value={
            "id": self.node_id,
            "kind": self.kind,
            "source": {
                "file": self.source_file,
                "line": self.source_line,
                "symbol": self.source_symbol,
            }
        })
'''
    (COMPONENTS_DIR / "simplicio_flow_node.py").write_text(flow_node_code, encoding="utf-8")

    map_reader_code = '''"""Simplicio Map Reader custom component for Langflow 1.12."""
import json
from pathlib import Path
try:
    from langflow.custom import Component
    from langflow.io import Output, StrInput
    from langflow.schema import Data
except ImportError:
    class Component: pass
    Output = StrInput = Data = object

class SimplicioMapReader(Component):
    display_name = "Simplicio Map Reader"
    description = "Reads .simplicio/ or docs/flow/ artifacts into Langflow"
    icon = "folder-search"

    inputs = [
        StrInput(name="flow_json_path", display_name="Flow JSON Path", value="docs/flow/simplicio-local.flow.json"),
    ]

    outputs = [
        Output(display_name="Flow Payload", name="payload", method="read_flow"),
    ]

    def read_flow(self) -> Data:
        path = Path(self.flow_json_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            return Data(value={"error": f"Path not found: {path}"})
        with open(path, "r", encoding="utf-8") as f:
            return Data(value=json.load(f))
'''
    (COMPONENTS_DIR / "simplicio_map_reader.py").write_text(map_reader_code, encoding="utf-8")


def render_images(mmd_file: Path, svg_file: Path, png_file: Path) -> dict[str, str]:
    """Render Mermaid diagram to SVG and PNG using mmdc, failing explicitly if blocked."""
    statuses = {"svg": "blocked(mmdc ausente)", "png": "blocked(mmdc ausente)"}

    puppeteer_cfg = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump({"args": ["--no-sandbox"]}, puppeteer_cfg)
        puppeteer_cfg.close()

        # Check if npx and @mermaid-js/mermaid-cli are available
        for target, out_path in [("svg", svg_file), ("png", png_file)]:
            cmd = [
                "npx", "-y", "@mermaid-js/mermaid-cli",
                "-i", str(mmd_file),
                "-o", str(out_path),
                "-p", puppeteer_cfg.name
            ]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if res.returncode == 0 and out_path.exists() and out_path.stat().st_size > 0:
                    statuses[target] = "ok"
                else:
                    err_msg = res.stderr.strip()[:100] or res.stdout.strip()[:100] or "unknown error"
                    statuses[target] = f"blocked({err_msg})"
            except FileNotFoundError:
                statuses[target] = "blocked(npx/mmdc not installed)"
            except subprocess.TimeoutExpired:
                statuses[target] = "blocked(mmdc timeout)"
            except Exception as ex:
                statuses[target] = f"blocked({ex})"
    finally:
        if os.path.exists(puppeteer_cfg.name):
            os.remove(puppeteer_cfg.name)

    return statuses


def push_to_langflow(langflow_url: str, flow_payload: dict[str, Any]) -> tuple[bool, str]:
    """Push flow to a running Langflow instance and verify retrieval."""
    url = langflow_url.rstrip("/") + "/api/v1/flows/"
    data = json.dumps(flow_payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8")
            res_json = json.loads(body)
            flow_id = res_json.get("id")
            if not flow_id:
                return False, f"Langflow POST succeeded but returned no flow ID: {body[:200]}"
            
            # Verify retrieval with GET
            get_req = urllib.request.Request(f"{url}{flow_id}", method="GET")
            with urllib.request.urlopen(get_req, timeout=5) as get_resp:
                if 200 <= get_resp.status < 300:
                    return True, f"Imported flow ID {flow_id} verified via GET"
                return False, f"GET verification failed with status {get_resp.status}"
    except urllib.error.URLError as e:
        return False, f"Langflow unreachable at {url}: {e}"
    except Exception as e:
        return False, f"Error pushing to Langflow: {e}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate simplicio-local flow artifacts.")
    parser.add_argument("--push-langflow", help="Langflow host to push flow (e.g. http://localhost:7860)")
    parser.add_argument("--check-drift", action="store_true", help="Only validate drift and exit.")
    args = parser.parse_args()

    FLOW_DIR.mkdir(parents=True, exist_ok=True)
    LANGFLOW_DIR.mkdir(parents=True, exist_ok=True)

    if FLOW_JSON_PATH.exists():
        with open(FLOW_JSON_PATH, "r", encoding="utf-8") as f:
            flow_data = json.load(f)
    else:
        flow_data = get_default_flow_data()

    # 1. Check Drift
    drift_errors = validate_drift(flow_data)
    if drift_errors:
        print("ERROR: Drift detected in flow.json:", file=sys.stderr)
        for err in drift_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    if args.check_drift:
        print("Drift check passed successfully.")
        return 0

    # 2. Save deterministic flow.json
    json_bytes = json.dumps(flow_data, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"
    FLOW_JSON_PATH.write_bytes(json_bytes)
    print(f"✔ Saved: {FLOW_JSON_PATH.relative_to(REPO_ROOT)}")

    # 3. Generate Mermaid .mmd
    mmd_content = build_mermaid(flow_data)
    MMD_PATH.write_text(mmd_content, encoding="utf-8")
    print(f"✔ Saved: {MMD_PATH.relative_to(REPO_ROOT)}")

    # 4. Render Images (SVG / PNG)
    img_statuses = render_images(MMD_PATH, SVG_PATH, PNG_PATH)
    print(f"  SVG status: {img_statuses['svg']}")
    print(f"  PNG status: {img_statuses['png']}")

    # 5. Generate Langflow flow JSON
    langflow_payload = build_langflow_json(flow_data)
    langflow_bytes = json.dumps(langflow_payload, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"
    LANGFLOW_JSON_PATH.write_bytes(langflow_bytes)
    print(f"✔ Saved: {LANGFLOW_JSON_PATH.relative_to(REPO_ROOT)}")

    # 6. Emit helper components
    emit_langflow_components()
    print(f"✔ Emitted Langflow custom components in: {COMPONENTS_DIR.relative_to(REPO_ROOT)}")

    # 7. Optional Push to Langflow
    if args.push_langflow:
        success, msg = push_to_langflow(args.push_langflow, langflow_payload)
        print(f"  Langflow Push: {'SUCCESS' if success else 'BLOCKED'} ({msg})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
