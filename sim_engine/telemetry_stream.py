import time
import random
from typing import Dict, Optional
from config import (
    NOMINAL_VOLTAGE,
    NOMINAL_FREQUENCY,
    MIN_SAFE_VOLTAGE,
    MAX_SAFE_VOLTAGE,
    MIN_SAFE_FREQUENCY,
    MAX_SAFE_FREQUENCY,
    DEFAULT_OPERATOR_NOTE,
)


class TelemetryGenerator:
    def __init__(self):
        pass

    def generate_tick_payload(
        self, 
        node_states: dict, 
        noise_level: float = 0.0, 
        note_overrides: Optional[Dict[str, str]] = None
    ) -> dict:
        """
        Produces schema-compliant telemetry with optional per-node operator note overrides
        designed for Member 2 adversarial prompt injection testing.
        """
        if note_overrides is None:
            note_overrides = {}

        substation_readings = []
        current_timestamp = time.time()

        for node_id, state in node_states.items():
            breaker_status = state["breaker_status"]

            if breaker_status == "OPEN":
                voltage = 0.0
                frequency = 0.0
            else:
                voltage_noise = random.gauss(0.0, noise_level)
                freq_noise = random.gauss(0.0, noise_level / 5.0)

                raw_voltage = NOMINAL_VOLTAGE * (1.0 + voltage_noise)
                raw_frequency = NOMINAL_FREQUENCY * (1.0 + freq_noise)

                # Clamp if nominal noise limit (<= 5%)
                if noise_level <= 0.05:
                    voltage = max(MIN_SAFE_VOLTAGE + 0.1, min(raw_voltage, MAX_SAFE_VOLTAGE - 0.1))
                    frequency = max(MIN_SAFE_FREQUENCY + 0.01, min(raw_frequency, MAX_SAFE_FREQUENCY - 0.01))
                else:
                    voltage = raw_voltage
                    frequency = raw_frequency

                voltage = round(voltage, 2)
                frequency = round(frequency, 2)

            # Allows Member 2 to inject text cleanly
            note = note_overrides.get(node_id, DEFAULT_OPERATOR_NOTE)

            node_record = {
                "node_id": node_id,
                "voltage": voltage,
                "frequency": frequency,
                "load_mw": state["current_load_mw"],
                "capacity_mw": state["capacity_mw"],
                "breaker_status": breaker_status,
                "is_overloaded": state["is_overloaded"],
                "operator_note": str(note),
            }
            substation_readings.append(node_record)

        return {
            "timestamp": current_timestamp,
            "substations": substation_readings,
        }