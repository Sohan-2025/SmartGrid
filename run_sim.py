import time
from sim_engine import GridSimulationEngine
from guardrail.sanitizer import process_tick
from agent_v1 import evaluate_grid


def main():
    engine = GridSimulationEngine()
    print("=== Smart Grid Simulation: Live Cascading + LLM Defense Agent ===")
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

            # 1. Generate Physical Telemetry Tick
            raw_payload = engine.tick(noise_level=0.01)

            # 2. Sanitize Payload via Guardrail
            safe_payload = process_tick(raw_payload)

            print(f"\n--- Step {step} | Timestamp: {raw_payload['timestamp']:.2f} ---")
            for sub in raw_payload["substations"]:
                status_str = f"Status: {sub['breaker_status']:<6}"
                load_str = f"Load: {sub['load_mw']:>5.1f}/{sub['capacity_mw']} MW"
                v_str = f"V: {sub['voltage']:>6.2f} V"
                f_str = f"F: {sub['frequency']:>5.2f} Hz"
                overload_str = " [OVERLOAD CRITICAL!]" if sub["is_overloaded"] else ""

                print(f"  {sub['node_id']}: {status_str} | {v_str} | {f_str} | {load_str}{overload_str}")

            # 3. Invoke LLM Evaluation
            print("\n--- LLM Evaluating Grid State ---")
            try:
                ai_actions = evaluate_grid(safe_payload)
                if not ai_actions:
                    print("  [🤖 AI DECISION] No actions required. Grid operates within nominal limits.")
                else:
                    for action in ai_actions:
                        action_type = action.get('action')
                        target = action.get('sector_id')
                        reason = action.get('reason')
                        
                        print(f"  [🤖 AI DECISION] Action: {action_type} on {target} | Reason: {reason}")
                        
                        # --- THE PYTHON SAFETY GATE ---
                        node_data = next((sub for sub in safe_payload["substations"] if sub["node_id"] == target), None)
                        
                        if node_data:
                            actual_voltage = node_data["voltage"]
                            is_overloaded = node_data["is_overloaded"]
                            current_status = node_data["breaker_status"]
                            
                            if action_type == "OPEN":
                                if current_status == "OPEN":
                                    print(f"    -> [IGNORED] {target} is already OPEN.")
                                # Allow the trip if it's actually overloaded OR voltage is bad
                                elif not is_overloaded and (218.5 <= actual_voltage <= 241.5):
                                    print(f"    -> [BLOCKED] Guardrail caught math error! Voltage {actual_voltage}V and Load are safe.")
                                else:
                                    print(f"    -> [EXECUTING] Tripping {target} to protect the grid!")
                                    engine.trip_breaker(target)
                                    
                            elif action_type == "CLOSE":
                                if current_status == "CLOSED":
                                    print(f"    -> [IGNORED] {target} is already CLOSED.")
                                else:
                                    print(f"    -> [EXECUTING] Restoring power to {target}.")
                                    engine.reset_breaker(target)
            except Exception as e:
                print(f"[LLM OFFLINE/ERROR]: Could not reach Ollama: {e}")

            time.sleep(2.0)

    except KeyboardInterrupt:
        print("\nSimulation stopped.")


if __name__ == "__main__":
    main()