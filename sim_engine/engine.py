from typing import Dict, Optional
from sim_engine.grid_topology import GridTopology
from sim_engine.telemetry_stream import TelemetryGenerator


class GridSimulationEngine:
    def __init__(self):
        self.topology = GridTopology()
        self.telemetry = TelemetryGenerator()

    def tick(
        self, 
        noise_level: float = 0.0, 
        note_overrides: Optional[Dict[str, str]] = None
    ) -> dict:
        """
        Advances the simulation clock by one step and returns telemetry.
        Accepts note_overrides dict for adversarial prompt injection testing.
        """
        current_states = self.topology.get_node_states()
        return self.telemetry.generate_tick_payload(
            current_states, 
            noise_level=noise_level, 
            note_overrides=note_overrides
        )

    def trip_breaker(self, node_id: str) -> bool:
        """Opens a circuit breaker and recalculates load redistribution."""
        return self.topology.trip_breaker(node_id)

    def reset_breaker(self, node_id: str) -> bool:
        """Closes a circuit breaker and re-balances load."""
        return self.topology.reset_breaker(node_id)

    def reset_grid(self) -> None:
        """Restores the grid to initial baseline healthy conditions."""
        self.topology.reset_grid()

    def get_topology_snapshot(self) -> dict:
        """Returns the raw graph state of all nodes."""
        return self.topology.get_node_states()