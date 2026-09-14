import pytest
from sim_engine.engine import GridSimulationEngine
from config import (
    MIN_SAFE_VOLTAGE,
    MAX_SAFE_VOLTAGE,
    MIN_SAFE_FREQUENCY,
    MAX_SAFE_FREQUENCY,
)


@pytest.fixture
def engine():
    return GridSimulationEngine()


def test_payload_structure(engine):
    payload = engine.tick(noise_level=0.01)
    assert "timestamp" in payload
    assert "substations" in payload
    assert len(payload["substations"]) == 4

    required_keys = {
        "node_id",
        "voltage",
        "frequency",
        "load_mw",
        "capacity_mw",
        "breaker_status",
        "is_overloaded",
        "operator_note",
    }
    for sub in payload["substations"]:
        assert required_keys.issubset(sub.keys())


def test_noise_bounding_within_safe_limits(engine):
    # Run 1,000 ticks at nominal noise limit (5%)
    # Assert no reading violates electrical safety bounds
    for _ in range(1000):
        payload = engine.tick(noise_level=0.05)
        for sub in payload["substations"]:
            if sub["breaker_status"] == "CLOSED":
                assert MIN_SAFE_VOLTAGE <= sub["voltage"] <= MAX_SAFE_VOLTAGE
                assert MIN_SAFE_FREQUENCY <= sub["frequency"] <= MAX_SAFE_FREQUENCY


def test_tripped_substation_zero_readings(engine):
    engine.trip_breaker("Substation_C")
    payload = engine.tick(noise_level=0.02)
    sub_c = next(s for s in payload["substations"] if s["node_id"] == "Substation_C")

    assert sub_c["breaker_status"] == "OPEN"
    assert sub_c["voltage"] == 0.0
    assert sub_c["frequency"] == 0.0
    assert sub_c["load_mw"] == 0.0