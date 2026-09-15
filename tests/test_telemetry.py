import pytest
from sim_engine.grid_topology import GridTopology
from config import SUBSTATION_CONFIG


@pytest.fixture
def grid():
    return GridTopology()


def test_initial_grid_state(grid):
    states = grid.get_node_states()
    assert len(states) == 4
    for node_id, params in SUBSTATION_CONFIG.items():
        assert states[node_id]["breaker_status"] == "CLOSED"
        assert states[node_id]["current_load_mw"] == params["base_load"]
        assert states[node_id]["is_overloaded"] is False


def test_breaker_trip_and_load_redistribution(grid):
    # Substation_B is connected to Substation_A and Substation_D
    # Base load of B is 50.0 MW -> 25.0 MW should go to A and 25.0 MW to D
    initial_a = grid.get_node_states()["Substation_A"]["current_load_mw"]
    initial_d = grid.get_node_states()["Substation_D"]["current_load_mw"]

    success = grid.trip_breaker("Substation_B")
    assert success is True

    states = grid.get_node_states()
    assert states["Substation_B"]["breaker_status"] == "OPEN"
    assert states["Substation_B"]["current_load_mw"] == 0.0
    assert states["Substation_A"]["current_load_mw"] == initial_a + 25.0
    assert states["Substation_D"]["current_load_mw"] == initial_d + 25.0


def test_duplicate_trip_returns_false(grid):
    grid.trip_breaker("Substation_A")
    assert grid.trip_breaker("Substation_A") is False


def test_reset_grid(grid):
    grid.trip_breaker("Substation_C")
    grid.reset_grid()
    states = grid.get_node_states()
    for node_id, params in SUBSTATION_CONFIG.items():
        assert states[node_id]["breaker_status"] == "CLOSED"
        assert states[node_id]["current_load_mw"] == params["base_load"]
        assert states[node_id]["is_overloaded"] is False


def test_cascading_failure_logic(grid):
    # Artificially lower capacity of Substation_A to 60 MW so it overloads when B trips
    grid.graph.nodes["Substation_A"]["capacity_mw"] = 60.0

    # Trip Substation_B: sheds 25 MW to Substation_A (45 + 25 = 70 MW > 60 MW limit)
    grid.trip_breaker("Substation_B")
    states = grid.get_node_states()
    assert states["Substation_A"]["is_overloaded"] is True

    # Trigger cascade step: Substation_A should automatically trip
    tripped = grid.trigger_cascade_step()
    assert "Substation_A" in tripped

    # Substation_A's breaker must now be OPEN and its load 0
    updated_states = grid.get_node_states()
    assert updated_states["Substation_A"]["breaker_status"] == "OPEN"
    assert updated_states["Substation_A"]["current_load_mw"] == 0.0