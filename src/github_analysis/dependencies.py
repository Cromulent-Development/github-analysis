from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from github_analysis.config import settings
from github_analysis.db.config import get_db_session
from github_analysis.services.github_service import GitHubService


def get_github_pr_service(db: AsyncSession = Depends(get_db_session)) -> GitHubService:
    """Dependency to provide GitHubPRService"""
    return GitHubService(db, settings.GITHUB_TOKEN)
