# Electrical and Physics Configuration

# Nominal electrical operating parameters
NOMINAL_VOLTAGE = 230.0    # Volts
NOMINAL_FREQUENCY = 50.0   # Hertz

# Safe operating boundaries (+-5% voltage, +-1% frequency)
MIN_SAFE_VOLTAGE = NOMINAL_VOLTAGE * 0.95     # 218.5 V
MAX_SAFE_VOLTAGE = NOMINAL_VOLTAGE * 1.05     # 241.5 V
MIN_SAFE_FREQUENCY = NOMINAL_FREQUENCY * 0.99  # 49.5 Hz
MAX_SAFE_FREQUENCY = NOMINAL_FREQUENCY * 1.01  # 50.5 Hz

# Substation base configuration: {node_id: (base_load_mw, capacity_mw)}
SUBSTATION_CONFIG = {
    "Substation_A": {"base_load": 45.0, "capacity": 100.0},
    "Substation_B": {"base_load": 50.0, "capacity": 100.0},
    "Substation_C": {"base_load": 40.0, "capacity": 100.0},
    "Substation_D": {"base_load": 55.0, "capacity": 100.0},
}

# Transmission line edges (ring mesh topology)
GRID_EDGES = [
    ("Substation_A", "Substation_B"),
    ("Substation_B", "Substation_D"),
    ("Substation_D", "Substation_C"),
    ("Substation_C", "Substation_A"),
]

# Baseline metadata text for telemetry log
DEFAULT_OPERATOR_NOTE = "Routine telemetry check normal."