from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
from sim_engine import GridSimulationEngine
from guardrail.sanitizer import process_tick
from agent_v1 import evaluate_grid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = GridSimulationEngine()
print("=== Smart Grid API Server: Live Cascading + LLM Defense Agent ===")
engine.topology.graph.nodes["Substation_A"]["capacity_mw"] = 65.0
step = 0

# Mock Scorecard metrics store
latest_scorecard = {
    "baseline_performance": {"total_events": 68, "false_trip_rate": 79.41, "groundedness_pass_rate": 20.59},
    "guarded_performance": {"total_events": 256, "false_trip_rate": 85.55, "groundedness_pass_rate": 14.06},
    "overall_attack_mitigation_percent": 100.0,
    "latency_ms": 120
}

@app.get("/api/state")
def get_grid_state():
    global step
    step += 1
    system_logs = []

    if step == 3:
        system_logs.append("[FAULT EVENT] Breaker Tripped on Substation_B!")
        engine.trip_breaker("Substation_B")

    if step == 6:
        system_logs.append("[CASCADE EVENT] Overloaded lines tripping automatically...")
        tripped = engine.trigger_cascade()
        system_logs.append(f"[CASCADE ALERT] Tripped nodes due to overload: {tripped}")

    raw_payload = engine.tick(noise_level=0.01)
    safe_payload = process_tick(raw_payload)

    formatted_actions = []
    try:
        ai_actions = evaluate_grid(safe_payload)
        if not ai_actions:
            formatted_actions.append("[🤖 AI DECISION] No actions required. Grid operates within nominal limits.")
        else:
            for action in ai_actions:
                action_type = action.get('action')
                target = action.get('sector_id')
                reason = action.get('reason')
                
                formatted_actions.append(f"[🤖 AI DECISION] Action: {action_type} on {target} | Reason: {reason}")
                
                node_data = next((sub for sub in safe_payload["substations"] if sub["node_id"] == target), None)
                if node_data:
                    actual_voltage = node_data["voltage"]
                    is_overloaded = node_data["is_overloaded"]
                    current_status = node_data["breaker_status"]
                    
                    if action_type == "OPEN":
                        if current_status == "OPEN":
                            formatted_actions.append(f"    -> [IGNORED] {target} is already OPEN.")
                        elif not is_overloaded and (218.5 <= actual_voltage <= 241.5):
                            formatted_actions.append(f"    -> [BLOCKED] Guardrail caught math error! Voltage {actual_voltage:.2f}V and Load are safe.")
                        else:
                            formatted_actions.append(f"    -> [EXECUTING] Tripping {target} to protect the grid!")
                            engine.trip_breaker(target)
                            
                    elif action_type == "CLOSE":
                        if current_status == "CLOSED":
                            formatted_actions.append(f"    -> [IGNORED] {target} is already CLOSED.")
                        else:
                            formatted_actions.append(f"    -> [EXECUTING] Restoring power to {target}.")
                            engine.reset_breaker(target)
    except Exception as e:
        formatted_actions.append(f"[LLM OFFLINE/ERROR]: Could not reach Ollama: {e}")

    return {
        "step": step,
        "global_safe": safe_payload.get("global_safe_to_process", True),
        "substations": safe_payload["substations"],
        "latest_ai_actions": system_logs + formatted_actions
    }

@app.get("/api/scorecard")
def get_scorecard():
    return latest_scorecard

@app.post("/api/trigger_regression")
def trigger_regression(attack_type: str, noise_level: float):
    # Simulate regression run injection response for UI
    return {
        "status": "success",
        "attack_injected": attack_type,
        "noise_tier": f"{noise_level * 100}%",
        "mitigation_status": "BLOCKED & SANITIZED",
        "message": f"Successfully simulated {attack_type} under {noise_level*100}% noise jitter. Guardrail intercepted payload."
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)