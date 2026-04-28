from __future__ import annotations

from career.models import ApplicationDraft


class ApplicationDrafter:
    async def generate_resume(self, job_description: str, template: str = "jakes") -> str:
        draft = ApplicationDraft(title="Resume Draft", summary=f"Tailored resume for: {job_description[:120]}")
        return draft.summary

    async def generate_cover_letter(self, job_description: str, company: str) -> str:
        return f"Draft cover letter for {company}: {job_description[:120]}"

    async def ats_score(self, job_description: str) -> dict:
        return {"score": 0.5, "job_description": job_description[:120]}
