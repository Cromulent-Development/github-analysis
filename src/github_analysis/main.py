from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from github_analysis.db.config import  get_db_session
from github_analysis.dependencies import get_github_service
from github_analysis.services.github import GitHubService


app = FastAPI(title="GitHub Analysis")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/test-github")
async def test_github(
        github_service: GitHubService = Depends(get_github_service)
):
    """Temporary endpoint to test GitHub API responses"""
    prs = await github_service.get_pull_requests("python", "cpython", state="closed", per_page=1)
    comments = await github_service.get_pr_comments("python", "cpython", prs[0]["number"])
    diff = await github_service.get_pr_diff("python", "cpython", prs[0]["number"])

    return {
        "pull_request": prs[0],
        "comments": comments[:2] if comments else [],
        "diff_preview": diff[:500] if diff else ""
    }


@app.get("/health/db")
async def test_db_connection(db: AsyncSession = Depends(get_db_session)):
    try:
        result = await db.execute(text("SELECT 1"))
        db_status = result.scalar()
        return {
            "status": "Database connected successfully",
            "db_response": db_status
        }
    except Exception as e:
        return {
            "status": "Database connection failed",
            "error": str(e)
        }