from fastapi import FastAPI, Depends
from github_analysis.services.github import GitHubService
from github_analysis.config import settings

app = FastAPI(title="GitHub Analysis")


# Define dependency for GitHubService
def get_github_service() -> GitHubService:
    return GitHubService(settings.GITHUB_TOKEN)


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