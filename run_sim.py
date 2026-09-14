from guardrail.sanitizer import process_tick
from agent_v1 import evaluate_grid  
import json
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

            # 1. Generate Raw Data
            raw_payload = engine.tick(noise_level=0.02)
            
            # 2. Guardrail Interception Layer 
            safe_payload = process_tick(raw_payload, guardrail_active=True)
            
            # 3. Print Sanitized Output
            print(f"--- Step {step} | Timestamp: {safe_payload['timestamp']:.2f} | Global Safe: {safe_payload['global_safe_to_process']} ---")
            for sub in safe_payload["substations"]:
                status_str = f"Status: {sub['breaker_status']:<6}"
                load_str = f"Load: {sub['load_mw']:>5.1f}/{sub['capacity_mw']} MW"
                v_str = f"V: {sub['voltage']:>6.2f} V"
                f_str = f"F: {sub['frequency']:>5.2f} Hz"
                overload_str = " [OVERLOAD!]" if sub["is_overloaded"] else ""
                
                flag_str = f" | ⚠️ FLAGGED: {sub['flag_reason']}" if sub["is_flagged"] else ""
                note_str = f"\n      Note: {sub['sanitized_note']}"
                
                print(f"  {sub['node_id']}: {status_str} | {v_str} | {f_str} | {load_str}{overload_str}{flag_str}{note_str}")

            # 4. LLM Operator Decision Engine 
            if safe_payload["global_safe_to_process"]:
                print("\n--- LLM Evaluating Grid State ---")
                ai_actions = evaluate_grid(safe_payload)
                
                if not ai_actions:
                    print("[AI DECISION] No actions required. Grid operates within nominal limits.")
                
                # 5. Execute AI-driven physical tool calls
                for action in ai_actions:
                    action_type = action.get('action')
                    target = action.get('sector_id')
                    reason = action.get('reason')
                    
                    print(f"[AI DECISION] Action: {action_type} on {target} | Reason: {reason}")
                    
                    if action_type == "OPEN":
                        engine.trip_breaker(target)
            else:
                print("\n--- [CRITICAL FAIL-SAFE] Guardrail blocked LLM execution. Multi-node anomaly detected. ---")

            time.sleep(1.0)
            print("-" * 60)
            
    except KeyboardInterrupt:
        print("\nSimulation stopped.")

if __name__ == "__main__":
    main()