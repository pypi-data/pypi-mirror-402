import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Skills and their call counts
skills = [
    ("commit", 42),
    ("review-pr", 18),
    ("lint-fix", 12),
    ("format-code", 8),
    ("test", 7),
    ("deploy", 5),
    ("rollback", 3)
]

# Subagents and their call counts
subagents = [
    ("code-generator", 20),
    ("test-runner", 15),
    ("debugger", 11),
    ("linter", 8),
    ("optimizer", 6),
    ("validator", 5),
    ("security-scanner", 4)
]

# Calculate total calls
total_calls = sum(count for _, count in skills) + sum(count for _, count in subagents)
print(f"Generating {total_calls} tool calls...")
print(f"  - {sum(count for _, count in skills)} Skills")
print(f"  - {sum(count for _, count in subagents)} Subagents")

# Output file path
output_path = Path.home() / ".claude" / "projects" / "test-ccpulse" / "test-session.jsonl"
output_path.parent.mkdir(parents=True, exist_ok=True)

# Base timestamp: 2026-01-17 08:00:00 UTC
base_time = datetime(2026, 1, 17, 8, 0, 0)

# Time window: 12 hours (08:00 to 20:00 UTC)
time_window_minutes = 12 * 60  # 720 minutes

def generate_timestamp(index, total):
    """Generate a timestamp distributed across the time window"""
    minutes_offset = int((index / total) * time_window_minutes)
    # Add some randomness within each slot
    import random
    minutes_offset += random.randint(-5, 5)
    minutes_offset = max(0, min(time_window_minutes, minutes_offset))

    timestamp = base_time + timedelta(minutes=minutes_offset)
    # Format as ISO 8601 with timezone
    return timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"

def create_skill_entry(skill_name, timestamp):
    """Create a JSONL entry for a Skill tool call"""
    return {
        "type": "assistant",
        "timestamp": timestamp,
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": f"toolu_{skill_name}_{timestamp.replace(':', '').replace('.', '')}",
                    "name": "Skill",
                    "input": {
                        "skill": skill_name
                    }
                }
            ]
        }
    }

def create_subagent_entry(subagent_type, timestamp):
    """Create a JSONL entry for a Task (subagent) tool call"""
    return {
        "type": "assistant",
        "timestamp": timestamp,
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": f"toolu_{subagent_type}_{timestamp.replace(':', '').replace('.', '')}",
                    "name": "Task",
                    "input": {
                        "subagent_type": subagent_type,
                        "prompt": f"Running {subagent_type} task",
                        "description": f"Test {subagent_type}"
                    }
                }
            ]
        }
    }

# Generate all entries
entries = []
index = 0

# Generate skills
for skill_name, count in skills:
    for _ in range(count):
        timestamp = generate_timestamp(index, total_calls)
        entries.append(create_skill_entry(skill_name, timestamp))
        index += 1

# Generate subagents
for subagent_type, count in subagents:
    for _ in range(count):
        timestamp = generate_timestamp(index, total_calls)
        entries.append(create_subagent_entry(subagent_type, timestamp))
        index += 1

# Sort by timestamp to make it more realistic
entries.sort(key=lambda x: x["timestamp"])

# Write to JSONL file
with open(output_path, 'w', encoding='utf-8') as f:
    for entry in entries:
        f.write(json.dumps(entry) + '\n')

print(f"\n[OK] Generated {len(entries)} entries")
print(f"[OK] Saved to: {output_path}")
print(f"\nData distribution:")
print("  Skills:")
for skill_name, count in skills:
    print(f"    - {skill_name}: {count}")
print("  Subagents:")
for subagent_type, count in subagents:
    print(f"    - {subagent_type}: {count}")
