import shutil
from pathlib import Path

from agent.dp_brain import DPBrain
from agent.models import ActionResult, PermissionScope, RiskTier, TaskNode
from agent.policy import PolicyEngine
from agent.runtime import AgentRuntime


class _Executor:
    def execute_node(self, node):
        return ActionResult(status="success", summary=f"ok:{node.node_id}")


def _tmp_dir(name: str) -> Path:
    base = Path.cwd() / "tests" / ".tmp_dp" / name
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)
    return base


def test_runtime_updates_dp_reward_and_checkpoint():
    temp_dir = _tmp_dir("runtime_integration")
    brain = DPBrain(db_path=temp_dir / "dp.sqlite3")
    runtime = AgentRuntime(
        executor=_Executor(),
        dp_brain=brain,
        policy=PolicyEngine(granted_scopes=set(PermissionScope)),
    )
    nodes = [
        TaskNode(
            node_id="step-1",
            objective="Open WhatsApp",
            tool="open_app",
            parameters={"app_name": "WhatsApp"},
            expected_outcome="WhatsApp opens",
            risk_tier=RiskTier.TIER_1,
        ),
        TaskNode(
            node_id="step-2",
            objective="Open Rajaa chat",
            tool="send_message",
            parameters={"receiver": "Rajaa", "message_text": "", "platform": "WhatsApp", "mode": "open_chat"},
            expected_outcome="Chat opens",
            risk_tier=RiskTier.TIER_1,
            depends_on=["step-1"],
        ),
    ]

    results = runtime.run(nodes, goal="Open WhatsApp and open Rajaa chat")

    assert all(result.status == "success" for result in results)
    checkpoint = brain.checkpoint_manager.load("Open WhatsApp and open Rajaa chat")
    assert checkpoint is not None
    assert checkpoint["completed_steps"] == 2
    metrics = brain.metrics.snapshot()
    assert metrics["events_recorded"] >= 1
    brain.close()
    shutil.rmtree(temp_dir)
