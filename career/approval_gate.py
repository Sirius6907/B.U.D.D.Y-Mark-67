from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class ApprovalDraft:
    action_type: str
    title: str
    body: str


class CareerApprovalGate:
    def __init__(self, approval_callback: Callable[[str], bool] | None = None):
        self.approval_callback = approval_callback

    async def draft_and_approve(self, action_type: str, draft: dict, approval_callback: Callable | None = None) -> bool:
        callback = approval_callback or self.approval_callback
        if callback is None:
            return False
        title = draft.get("title") or action_type
        body = draft.get("body") or draft.get("summary") or ""
        return bool(callback(f"Approve {title}: {body}"))
