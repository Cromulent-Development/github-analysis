from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from qdrant_client import QdrantClient

from github_analysis.config import settings
from github_analysis.db.config import get_db_session
from github_analysis.services.github_service import GitHubService
from github_analysis.services.ai_service import AIService
from github_analysis.services.analysis_service import AnalysisService


def get_qdrant_client():
    return QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)


def get_ai_service():
    return AIService(settings.OPENAI_API_KEY)


def get_analysis_service(
    db: AsyncSession = Depends(get_db_session),
    qdrant: QdrantClient = Depends(get_qdrant_client),
    ai_service: AIService = Depends(get_ai_service),
) -> AnalysisService:
    return AnalysisService(db, qdrant, ai_service)


def get_github_service(db: AsyncSession = Depends(get_db_session)) -> GitHubService:
    return GitHubService(db, settings.GITHUB_TOKEN)
