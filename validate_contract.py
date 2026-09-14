import json
from sim_engine import GridSimulationEngine

def validate_payload_format():
    engine = GridSimulationEngine()
    payload = engine.tick(noise_level=0.01)

    # Load JSON schema
    with open("schemas/schema.json", "r") as f:
        schema = json.load(f)

    # Basic structural assert against schema required fields
    assert "timestamp" in payload, "Missing timestamp"
    assert "substations" in payload, "Missing substations array"
    assert len(payload["substations"]) == 4, "Substations array must have exactly 4 items"

    required_sub_fields = set(schema["properties"]["substations"]["items"]["required"])
    allowed_nodes = set(schema["properties"]["substations"]["items"]["properties"]["node_id"]["enum"])

    for sub in payload["substations"]:
        sub_keys = set(sub.keys())
        assert required_sub_fields.issubset(sub_keys), f"Substation missing required fields: {required_sub_fields - sub_keys}"
        assert sub["node_id"] in allowed_nodes, f"Invalid node_id: {sub['node_id']}"
        assert sub["breaker_status"] in ["CLOSED", "OPEN"], f"Invalid breaker_status: {sub['breaker_status']}"
        assert isinstance(sub["operator_note"], str), "operator_note must be a string"

    print(" Contract Verification Passed: Engine output strictly complies with schemas/schema.json")

if __name__ == "__main__":
    validate_payload_format()