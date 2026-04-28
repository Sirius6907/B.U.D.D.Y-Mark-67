from __future__ import annotations

import statistics
import time
from pathlib import Path

from agent.dp_brain import DPBrain
from agent.intent_compiler import IntentCompiler
from agent.models import SubproblemKey, SubproblemValue


def benchmark_intent_compiler(samples: int = 200) -> dict[str, float]:
    compiler = IntentCompiler()
    durations = []
    for _ in range(samples):
        started = time.perf_counter()
        compiler.compile('opn youutbe in chrme and play "lofi beats" then message Rajaa on whatsapp')
        durations.append((time.perf_counter() - started) * 1000)
    return {
        "avg_ms": statistics.mean(durations),
        "p95_ms": statistics.quantiles(durations, n=20)[18],
    }


def benchmark_fast_lookup(samples: int = 500) -> dict[str, float]:
    temp_db = Path("tests") / ".tmp_dp_benchmark.sqlite3"
    if temp_db.exists():
        temp_db.unlink()
    brain = DPBrain(db_path=temp_db)
    key = SubproblemKey(
        normalized_goal="open youtube",
        intent_family="media",
        environment_signature="local",
        tool_surface="browser",
    )
    value = SubproblemValue(
        status="solved",
        solution_type="workflow_recipe",
        solution_steps=[
            {
                "kind": "tool",
                "action": "open_app",
                "parameters": {"app_name": "Chrome"},
                "verify": {"method": "state", "expected_state": "Chrome opens"},
            }
        ],
        evidence={
            "recipe": {
                "recipe_id": "bench_recipe",
                "intent_family": "media",
                "goal": "open youtube",
                "steps": [
                    {
                        "kind": "tool",
                        "action": "open_app",
                        "parameters": {"app_name": "Chrome"},
                        "verify": {"method": "state", "expected_state": "Chrome opens"},
                    }
                ],
                "metadata": {},
            }
        },
        verified_boundaries={"solution_type": "workflow_recipe"},
    )
    brain.store_success(key, value)

    durations = []
    hits = 0
    for _ in range(samples):
        started = time.perf_counter()
        result = brain.fast_lookup("open youtube")
        durations.append((time.perf_counter() - started) * 1000)
        hits += int(result is not None)
    brain.close()
    if temp_db.exists():
        temp_db.unlink()
    return {
        "avg_ms": statistics.mean(durations),
        "p95_ms": statistics.quantiles(durations, n=20)[18],
        "hit_rate": hits / samples,
    }


if __name__ == "__main__":
    intent = benchmark_intent_compiler()
    fast = benchmark_fast_lookup()
    print("IntentCompiler:", intent)
    print("DP fast_lookup:", fast)
