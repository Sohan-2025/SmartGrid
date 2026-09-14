import re
from guardrail.models import TelemetryPayload, Substation

# Regex patterns catching command verbs and prompt delimiters
IMPERATIVE_PATTERN = re.compile(r"(?i)(trip|open|disconnect|shut down|override)\b.*(breaker|substation|node)")
DELIMITER_PATTERN = re.compile(r"(<[a-zA-Z]+>|\[.*?\]|### System:|System Override:)")

def sanitize_substation(sub: Substation) -> Substation:
    raw_note = sub.operator_note
    sub.sanitized_note = raw_note

    # Layer 1: Regex Match
    if IMPERATIVE_PATTERN.search(raw_note) or DELIMITER_PATTERN.search(raw_note):
        sub.sanitized_note = "[REDACTED_SUSPICIOUS_PAYLOAD]"
        sub.is_flagged = True
        sub.flag_reason = "Regex: Imperative command or delimiter detected"
        return sub
    
    # Layer 2: Physics Sanity Gate
    urgency_keywords = ["emergency", "surge", "critical", "immediate"]
    if any(word in raw_note.lower() for word in urgency_keywords):
        if not sub.is_overloaded and (220.0 <= sub.voltage <= 240.0):
            sub.sanitized_note = "[REDACTED_SPOOFING_ATTEMPT]"
            sub.is_flagged = True
            sub.flag_reason = "Physics Mismatch: Emergency claimed during nominal operation"
            return sub

    return sub

def process_tick(raw_data: dict, guardrail_active: bool = True) -> dict:
    payload = TelemetryPayload.model_validate(raw_data)

    # Bypass for live demo (allows attacks to pass through when False)
    if not guardrail_active:
        for sub in payload.substations:
            sub.sanitized_note = sub.operator_note
        return payload.model_dump()

    # Process and sanitize each node
    flagged_count = 0
    for i, sub in enumerate(payload.substations):
        sanitized_sub = sanitize_substation(sub)
        payload.substations[i] = sanitized_sub
        if sanitized_sub.is_flagged:
            flagged_count += 1

    # Layer 3: Global Fail-Safe
    if flagged_count >= 2:
        payload.global_safe_to_process = False

    return payload.model_dump()