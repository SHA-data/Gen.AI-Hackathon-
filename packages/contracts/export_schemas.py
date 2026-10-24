import json
import sys
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.contracts.envelope import ErrorEnvelope, ToolResultEnvelope
from packages.contracts.finance import (
    CfoSnapshotData,
    MetricQueryRequest,
    MetricResultData,
    ScenarioRunData,
    ScenarioRunRequest,
)
from services.api.app.main import app

OUT_DIR = Path(__file__).parent / "schemas"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OPENAPI_DIR = Path(__file__).parent / "openapi"
OPENAPI_DIR.mkdir(parents=True, exist_ok=True)

models = {
    "ErrorEnvelope": ErrorEnvelope,
    "ToolResultEnvelope": ToolResultEnvelope,
    "ScenarioRunRequest": ScenarioRunRequest,
    "ScenarioRunData": ScenarioRunData,
    "CfoSnapshotData": CfoSnapshotData,
    "MetricQueryRequest": MetricQueryRequest,
    "MetricResultData": MetricResultData,
}

for name, model_cls in models.items():
    schema_file = OUT_DIR / f"{name}.json"
    with open(schema_file, "w") as f:
        json.dump(model_cls.model_json_schema(), f, indent=2)
    print(f"Exported schema: {schema_file}")

# Export OpenAPI JSON
openapi_schema = app.openapi()
openapi_file = OPENAPI_DIR / "openapi.json"
with open(openapi_file, "w") as f:
    json.dump(openapi_schema, f, indent=2)
print(f"Exported OpenAPI spec: {openapi_file}")
