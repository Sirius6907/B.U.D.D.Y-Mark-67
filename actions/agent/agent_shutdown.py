from __future__ import annotations

import asyncio
import concurrent.futures
import threading
import sys
import os
import time

from actions.base import Action, ActionRegistry
from agent.personality import (
    build_task_failed_reply,
    build_shutdown_farewell,
)
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result

class ShutdownBuddyAction(Action):
    @property
    def name(self) -> str:
        return "shutdown_buddy"

    @property
    def description(self) -> str:
        return (
            "Shuts down the assistant completely. "
            "Call this when the user expresses intent to end the conversation, "
            "close the assistant, say goodbye, or stop Buddy. "
            "The user can say this in ANY language."
        )

    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}}

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        if player:
            player.write_log("SYS: Shutdown requested.")
        farewell = build_shutdown_farewell()
        speech_future = None
        if speak:
            speech_future = speak(farewell)

        def _shutdown():
            if isinstance(speech_future, concurrent.futures.Future):
                try:
                    speech_future.result(timeout=15)
                except Exception:
                    pass
            else:
                time.sleep(1)
            try:
                if player and hasattr(player, "bridge"):
                    player.bridge.publish_shutdown_requested(farewell)
            except Exception:
                pass
            time.sleep(1.8)
            try:
                if player and hasattr(player, "root"):
                    player.root.quit()
            except Exception:
                pass
            time.sleep(4)
            os._exit(0)

        threading.Thread(target=_shutdown, daemon=True).start()
        
        return build_tool_result(
            tool_name=self.name,
            operation="shutdown",
            risk_level=RiskLevel.HIGH,
            status="success",
            summary="Shutting down the assistant",
            structured_data={"farewell_message": farewell},
            idempotent=False,
            preconditions=[],
            postconditions=["assistant terminating"],
        )

ActionRegistry.register(ShutdownBuddyAction)
