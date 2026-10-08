"""Simplicio Flow Node custom component for Langflow 1.12."""
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
