from __future__ import annotations

from agent.dp_brain import DPBrain, get_dp_brain
from agent.models import SubproblemKey


def build_subproblem_key(goal: str, context: dict | None = None) -> SubproblemKey:
    return get_dp_brain().state_encoder.build_key(goal, context)


class DPCore:
    def __init__(self, brain: DPBrain | None = None):
        self.brain = brain or get_dp_brain()

    def lookup(self, goal: str, context: dict | None = None):
        return self.brain.lookup(goal, context)

    def store_success(self, key, value, context: dict | None = None):
        self.brain.store_success(key, value)

    def store_partial(self, key, value, context: dict | None = None):
        self.brain.store_partial(key, value)

    def store_failure(self, key, value, context: dict | None = None):
        self.brain.store_failure(key, value)

    def note_reuse(self, hit):
        return hit

    def resume_or_decompose(self, goal: str, context: dict | None = None):
        return self.brain.compose(goal, context)


def get_dp_core() -> DPCore:
    return DPCore(get_dp_brain())
