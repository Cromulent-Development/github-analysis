from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from github_analysis.db.config import get_db_session
from github_analysis.dependencies import get_analysis_service, get_github_service
from github_analysis.services.analysis_service import AnalysisService
from github_analysis.services.github_service import GitHubService

app = FastAPI(title="GitHub Analysis")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/test-github")
async def test_github(
    db: AsyncSession = Depends(get_db_session),
    github_pr_service: GitHubService = Depends(get_github_service),
):
    """Temporary endpoint to test GitHub API responses and storage"""
    results = await github_pr_service.fetch_and_store_prs("python", "cpython", limit=5)
    return {"results": results, "message": "Data fetch and store attempted"}


@app.get("/health/db", response_model=None)  # Avoid response model validation here
async def test_db_connection(db: AsyncSession = Depends(get_db_session)):
    try:
        result = await db.execute(text("SELECT 1"))
        db_status = result.scalar()
        return {"status": "Database connected successfully", "db_response": db_status}
    except Exception as e:
        return {"status": "Database connection failed", "error": str(e)}


@app.post("/analyze-pr/{pr_id}")
async def analyze_pr(
    pr_id: int, analysis_service: AnalysisService = Depends(get_analysis_service)
):
    result = await analysis_service.process_pr(pr_id)
    return result
