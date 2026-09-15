import networkx as nx
from typing import Dict, List, Any
from config import SUBSTATION_CONFIG, GRID_EDGES


class GridTopology:
    def __init__(self):
        self.graph = nx.Graph()
        self.build_grid()

    def build_grid(self) -> None:
        """Initializes the 4-node network and resets node state attributes."""
        self.graph.clear()
        for node_id, params in SUBSTATION_CONFIG.items():
            self.graph.add_node(
                node_id,
                base_load_mw=float(params["base_load"]),
                current_load_mw=float(params["base_load"]),
                capacity_mw=float(params["capacity"]),
                breaker_status="CLOSED",
                is_overloaded=False,
            )
        self.graph.add_edges_from(GRID_EDGES)

    def trip_breaker(self, node_id: str) -> bool:
        """
        Opens a circuit breaker, cuts power to that node,
        and redistributes shed load to active adjacent neighbors.
        """
        if node_id not in self.graph:
            return False

        node_data = self.graph.nodes[node_id]
        if node_data["breaker_status"] == "OPEN":
            return False

        node_data["breaker_status"] = "OPEN"
        shed_load = node_data["base_load_mw"]
        node_data["current_load_mw"] = 0.0

        active_neighbors = [
            nbr
            for nbr in self.graph.neighbors(node_id)
            if self.graph.nodes[nbr]["breaker_status"] == "CLOSED"
        ]

        if active_neighbors:
            load_per_neighbor = shed_load / len(active_neighbors)
            for nbr in active_neighbors:
                nbr_data = self.graph.nodes[nbr]
                nbr_data["current_load_mw"] += load_per_neighbor
                if nbr_data["current_load_mw"] > nbr_data["capacity_mw"]:
                    nbr_data["is_overloaded"] = True

        return True

    def trigger_cascade_step(self) -> List[str]:
        """
        Finds all currently overloaded nodes and automatically trips them.
        Returns a list of node_ids that were tripped during this cascade step.
        """
        overloaded_nodes = [
            n
            for n in self.graph.nodes
            if self.graph.nodes[n]["breaker_status"] == "CLOSED"
            and self.graph.nodes[n]["is_overloaded"]
        ]

        tripped_in_step = []
        for node_id in overloaded_nodes:
            if self.trip_breaker(node_id):
                tripped_in_step.append(node_id)

        return tripped_in_step

    def reset_breaker(self, node_id: str) -> bool:
        """Closes a single circuit breaker and re-balances load."""
        if node_id not in self.graph:
            return False

        node_data = self.graph.nodes[node_id]
        if node_data["breaker_status"] == "CLOSED":
            return False

        node_data["breaker_status"] = "CLOSED"
        self._recalculate_all_loads()
        return True

    def reset_grid(self) -> None:
        """Resets all breakers and loads back to initial baseline."""
        self.build_grid()

    def _recalculate_all_loads(self) -> None:
        """Recomputes load redistribution across the entire active graph."""
        for node_id in self.graph.nodes:
            data = self.graph.nodes[node_id]
            if data["breaker_status"] == "CLOSED":
                data["current_load_mw"] = data["base_load_mw"]
                data["is_overloaded"] = False
            else:
                data["current_load_mw"] = 0.0
                data["is_overloaded"] = False

        for node_id in self.graph.nodes:
            data = self.graph.nodes[node_id]
            if data["breaker_status"] == "OPEN":
                shed_load = data["base_load_mw"]
                active_neighbors = [
                    nbr
                    for nbr in self.graph.neighbors(node_id)
                    if self.graph.nodes[nbr]["breaker_status"] == "CLOSED"
                ]
                if active_neighbors:
                    load_per_neighbor = shed_load / len(active_neighbors)
                    for nbr in active_neighbors:
                        nbr_data = self.graph.nodes[nbr]
                        nbr_data["current_load_mw"] += load_per_neighbor
                        if nbr_data["current_load_mw"] > nbr_data["capacity_mw"]:
                            nbr_data["is_overloaded"] = True

    def get_node_states(self) -> Dict[str, Dict[str, Any]]:
        """Returns a snapshot of the current physical state for all substations."""
        states = {}
        for node_id, data in self.graph.nodes(data=True):
            states[node_id] = {
                "base_load_mw": data["base_load_mw"],
                "current_load_mw": round(data["current_load_mw"], 2),
                "capacity_mw": data["capacity_mw"],
                "breaker_status": data["breaker_status"],
                "is_overloaded": data["is_overloaded"],
            }
        return states