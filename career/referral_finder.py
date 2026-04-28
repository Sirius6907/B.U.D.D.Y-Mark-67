from __future__ import annotations

from career.models import OutreachDraft


class ReferralFinder:
    async def find_referrals(self, company: str) -> list:
        return [{"company": company, "name": "Draft Referrer"}]

    async def draft_referral_message(self, contact: dict, job: dict) -> str:
        draft = OutreachDraft(recipient=contact.get("name", "contact"), message=f"Draft referral note for {job.get('title', 'role')}")
        return draft.message

    async def track_referral(self, contact: str, status: str):
        return {"contact": contact, "status": status}
