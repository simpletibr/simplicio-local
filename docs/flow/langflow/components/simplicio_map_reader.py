"""Simplicio Map Reader custom component for Langflow 1.12."""
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
