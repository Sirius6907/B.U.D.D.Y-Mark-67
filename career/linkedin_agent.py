from __future__ import annotations


class LinkedInAgent:
    async def get_profile_summary(self) -> dict:
        return {"status": "draft", "summary": "LinkedIn profile summary prepared for review."}

    async def suggest_profile_updates(self, job_target: str) -> list:
        return [f"Draft headline update for {job_target}", "Draft summary refresh", "Draft skills alignment"]

    async def draft_connection_request(self, username: str, reason: str) -> dict:
        return {"title": f"Connection request to {username}", "body": reason}

    async def search_people_at_company(self, company: str, role: str) -> list:
        return [{"company": company, "role": role, "name": "Draft Contact"}]
