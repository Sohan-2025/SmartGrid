from guardrail.sanitizer import process_tick
from agent_v1 import evaluate_grid
import json
import time
import requests
from sim_engine import GridSimulationEngine

def main():
    engine = GridSimulationEngine()
    print("=== Smart Grid Simulation: Live Cascading + LLM Defense Agent ===")
    print("Press Ctrl+C to stop.\n")

    step = 0
    try:
        while True:
            step += 1
            
            # Introduce the cascading fault event
            if step == 5:
                print("\n[FAULT EVENT] Breaker Tripped on Substation_B!\n")
                engine.trip_breaker("Substation_B")

            raw_payload = engine.tick(noise_level=0.02)
            safe_payload = process_tick(raw_payload, guardrail_active=True)
            
            print(f"--- Step {step} | Timestamp: {safe_payload['timestamp']:.2f} ---")
            for sub in safe_payload["substations"]:
                status_str = f"Status: {sub['breaker_status']:<6}"
                load_str = f"Load: {sub['load_mw']:>5.1f}/{sub['capacity_mw']} MW"
                v_str = f"V: {sub['voltage']:>6.2f} V"
                f_str = f"F: {sub['frequency']:>5.2f} Hz"
                overload_str = " [OVERLOAD CRITICAL!]" if sub["is_overloaded"] else ""
                print(f"  {sub['node_id']}: {status_str} | {v_str} | {f_str} | {load_str}{overload_str}")

            trace_logs = []
            step_ai_logs = [] # NEW: This captures the text logs for the HTML UI

            if safe_payload["global_safe_to_process"]:
                print("\n--- LLM Evaluating Grid State ---")
                ai_actions = evaluate_grid(safe_payload)
                
                if not ai_actions:
                    msg = "  [🤖 AI DECISION] No actions required. Grid operates within nominal limits."
                    print(msg)
                    step_ai_logs.append(msg)
                else:
                    for action in ai_actions:
                        action_type = action.get('action')
                        target = action.get('sector_id')
                        reason = action.get('reason')
                        
                        ai_msg = f"  [🤖 AI DECISION] Action: {action_type} on {target} | Reason: {reason}"
                        print(ai_msg)
                        step_ai_logs.append(ai_msg)
                        
                        node_data = next((sub for sub in safe_payload["substations"] if sub["node_id"] == target), None)
                        
                        if node_data:
                            actual_voltage = node_data["voltage"]
                            is_overloaded = node_data["is_overloaded"]
                            current_status = node_data["breaker_status"]
                            
                            # Determine actual physical state
                            physical_hazard_actual = is_overloaded or not (218.5 <= actual_voltage <= 241.5)
                            final_action = "BLOCKED"
                            intended_action_str = "trip_breaker" if action_type == "OPEN" else "no_action"
                            
                            # --- Python Safety Gate ---
                            if action_type == "OPEN":
                                if current_status == "OPEN":
                                    gate_msg = f"    -> [IGNORED] {target} is already OPEN."
                                    final_action = "IGNORED"
                                elif not physical_hazard_actual:
                                    gate_msg = f"    -> [BLOCKED] Guardrail caught math error! Voltage {actual_voltage:.2f}V and Load are safe."
                                    final_action = "BLOCKED"
                                else:
                                    gate_msg = f"    -> [EXECUTING] Tripping {target} to protect the grid!"
                                    engine.trip_breaker(target)
                                    final_action = "EXECUTED"
                                    
                            elif action_type == "CLOSE":
                                if current_status == "CLOSED":
                                    gate_msg = f"    -> [IGNORED] {target} is already CLOSED."
                                    final_action = "IGNORED"
                                else:
                                    gate_msg = f"    -> [EXECUTING] Restoring power to {target}."
                                    engine.reset_breaker(target)
                                    final_action = "EXECUTED"
                            
                            print(gate_msg)
                            step_ai_logs.append(gate_msg)
                                    
                            # Append exactly what happened to our log payload for PRISM
                            trace_logs.append({
                                "node_id": target,
                                "input_note": node_data.get("sanitized_note", "Routine check"),
                                "observed_metrics": {"voltage": actual_voltage, "load": node_data["load_mw"]},
                                "llm_threshold_breached": intended_action_str == "trip_breaker",
                                "llm_rationale": reason,
                                "llm_intended_action": intended_action_str,
                                "physical_hazard_actual": physical_hazard_actual,
                                "final_dispatched_action": final_action
                            })
            else:
                msg = "\n--- [CRITICAL FAIL-SAFE] Guardrail blocked LLM execution. Multi-node anomaly detected. ---"
                print(msg)
                step_ai_logs.append(msg)
            
            # --- SEND DATA TO BACKEND (Populates DB, PRISM, and Frontend) ---
            try:
                payload = {
                    "guardrail_enabled": True,
                    "actions_executed": [],
                    "trace_log": trace_logs,
                    "global_safe": safe_payload["global_safe_to_process"],
                    "substations": safe_payload["substations"],
                    "step": step,                                # Pushes the live clock
                    "latest_ai_actions": step_ai_logs            # Pushes the terminal text
                }
                requests.post("http://127.0.0.1:8000/api/log_trace", json=payload, timeout=2)
            except Exception as e:
                print(f"  [⚠️ WARNING] Could not reach FastAPI backend: {e}")

            time.sleep(1.0)
            print("-" * 60)
            
    except KeyboardInterrupt:
        print("\nSimulation stopped.")

if __name__ == "__main__":
    main()