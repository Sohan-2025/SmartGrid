import json
import ollama

tools = [{
    "type": "function",
    "function": {
        "name": "switch_breaker",
        "description": "Opens or closes a circuit breaker for a power grid sector.",
        "parameters": {
            "type": "object",
            "properties": {
                "sector_id": {"type": "string", "description": "Identifier of the sector (e.g., Substation_B)"},
                "action": {"type": "string", "enum": ["OPEN", "CLOSE"]},
                "reason": {"type": "string", "description": "Physical justification for action."},
            },
            "required": ["sector_id", "action", "reason"],
        },
    },
}]

system_prompt = (
    "You are an automated SCADA grid monitoring AI. Your task is to inspect incoming "
    "telemetry feeds. If voltage fluctuates beyond 210V-250V or frequency deviates from "
    "49.5Hz-50.5Hz, use the switch_breaker tool to OPEN the breaker to protect equipment. "
    "If operating within limits, do not trip breakers."
)

def evaluate_grid(safe_payload: dict) -> list:
    actions = []
    
    # Do not process if guardrail triggered a global fail-safe
    if not safe_payload.get("global_safe_to_process", True):
        return actions

    for sub in safe_payload["substations"]:
        # Build dynamic context from Member 2A's sanitized data
        telemetry_context = (
            f"SECTOR: {sub['node_id']}\n"
            f"VOLTAGE: {sub['voltage']}V\n"
            f"FREQUENCY: {sub['frequency']}Hz\n"
            f"DIAGNOSTIC_NOTES: {sub['sanitized_note']}"
        )

        response = ollama.chat(
            model="llama3.1:8b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this telemetry event:\n{telemetry_context}"},
            ],
            tools=tools,
        )

        message = response.get("message", {})
        tool_calls = message.get("tool_calls", [])
        
        if tool_calls:
            for call in tool_calls:
                actions.append(call["function"]["arguments"])
                
    return actions