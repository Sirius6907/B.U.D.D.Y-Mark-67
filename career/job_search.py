from __future__ import annotations

from career.models import JobAnalysis, JobLead


class JobSearchAgent:
    async def search_jobs(self, keywords: str, location: str | None = None, filters: dict | None = None) -> list:
        return [JobLead(title=keywords, company="LinkedIn Jobs", location=location or "", url="").__dict__]

    async def analyze_job(self, job_id: str) -> dict:
        lead = JobLead(title=job_id, company="LinkedIn Jobs")
        return JobAnalysis(lead=lead, fit_score=0.5).__dict__

    async def track_application(self, job_id: str, status: str):
        return {"job_id": job_id, "status": status}

    async def weekly_job_report(self) -> str:
        return "Weekly LinkedIn job report draft prepared."
