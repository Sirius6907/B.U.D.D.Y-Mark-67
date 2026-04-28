from __future__ import annotations


def search_jobs_workflow(query: str) -> dict:
    return {"intent": "search_jobs", "query": query}


def optimize_github_workflow(target: str) -> dict:
    return {"intent": "optimize_github", "target": target}


def apply_to_job_workflow(target: str) -> dict:
    return {"intent": "apply_to_job", "target": target}


def find_referrals_workflow(company: str) -> dict:
    return {"intent": "find_referrals", "company": company}
