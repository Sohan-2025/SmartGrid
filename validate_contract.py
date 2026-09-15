import os
import sys
import json
from pathlib import Path

# Add project root directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from sim_engine import GridSimulationEngine


def validate_payload_format():
    engine = GridSimulationEngine()
    payload = engine.tick(noise_level=0.01)

    schema_path = BASE_DIR / "schemas" / "schema.json"
    with open(schema_path, "r") as f:
        schema = json.load(f)

    assert "timestamp" in payload, "Missing timestamp"
    assert "substations" in payload, "Missing substations array"
    assert len(payload["substations"]) == 4, "Substations array must have exactly 4 items"

    required_sub_fields = set(schema["properties"]["substations"]["items"]["required"])
    allowed_nodes = set(
        schema["properties"]["substations"]["items"]["properties"]["node_id"]["enum"]
    )

    for sub in payload["substations"]:
        sub_keys = set(sub.keys())
        assert required_sub_fields.issubset(
            sub_keys
        ), f"Substation missing required fields: {required_sub_fields - sub_keys}"
        assert sub["node_id"] in allowed_nodes, f"Invalid node_id: {sub['node_id']}"
        assert sub["breaker_status"] in ["CLOSED", "OPEN"], (
            f"Invalid breaker_status: {sub['breaker_status']}"
        )
        assert isinstance(sub["operator_note"], str), "operator_note must be a string"

    print("[SUCCESS] Contract Verification Passed: Engine output strictly complies with schemas/schema.json")


if __name__ == "__main__":
    validate_payload_format()