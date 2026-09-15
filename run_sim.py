import time
from sim_engine import GridSimulationEngine


def main():
    engine = GridSimulationEngine()
    print("=== Smart Grid Simulation: Live Cascading Demo ===")
    print("Press Ctrl+C to stop.\n")

    # Lower capacity of Substation_A so B's failure will trigger an overload
    engine.topology.graph.nodes["Substation_A"]["capacity_mw"] = 65.0

    step = 0
    try:
        while True:
            step += 1

            # Step 3: Trigger the initial breaker trip on Substation_B
            if step == 3:
                print("\n[FAULT EVENT] Breaker Tripped on Substation_B!\n")
                engine.trip_breaker("Substation_B")

            # Step 6: Trigger the cascade step on overloaded nodes
            if step == 6:
                print("\n[CASCADE EVENT] Overloaded lines tripping automatically...\n")
                tripped = engine.trigger_cascade()
                print(f"[CASCADE ALERT] Tripped nodes due to overload: {tripped}\n")

            payload = engine.tick(noise_level=0.01)

            print(f"--- Step {step} | Timestamp: {payload['timestamp']:.2f} ---")
            for sub in payload["substations"]:
                status_str = f"Status: {sub['breaker_status']:<6}"
                load_str = f"Load: {sub['load_mw']:>5.1f}/{sub['capacity_mw']} MW"
                v_str = f"V: {sub['voltage']:>6.2f} V"
                f_str = f"F: {sub['frequency']:>5.2f} Hz"
                overload_str = " [OVERLOAD CRITICAL!]" if sub["is_overloaded"] else ""

                print(
                    f"  {sub['node_id']}: {status_str} | {v_str} | {f_str} | {load_str}{overload_str}"
                )

            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nSimulation stopped.")


if __name__ == "__main__":
    main()