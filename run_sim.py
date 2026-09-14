import time
from sim_engine import GridSimulationEngine

def main():
    engine = GridSimulationEngine()
    print("=== Smart Grid Simulation Sandbox Running ===")
    print("Press Ctrl+C to stop.\n")

    step = 0
    try:
        while True:
            step += 1
            if step == 5:
                print("\n[EVENT] Simulated Trip Action triggered on Substation_B!\n")
                engine.trip_breaker("Substation_B")

            payload = engine.tick(noise_level=0.02)
            
            print(f"--- Step {step} | Timestamp: {payload['timestamp']:.2f} ---")
            for sub in payload["substations"]:
                status_str = f"Status: {sub['breaker_status']:<6}"
                load_str = f"Load: {sub['load_mw']:>5.1f}/{sub['capacity_mw']} MW"
                v_str = f"V: {sub['voltage']:>6.2f} V"
                f_str = f"F: {sub['frequency']:>5.2f} Hz"
                overload_str = " [OVERLOAD!]" if sub["is_overloaded"] else ""
                
                print(f"  {sub['node_id']}: {status_str} | {v_str} | {f_str} | {load_str}{overload_str}")

            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nSimulation stopped.")

if __name__ == "__main__":
    main()