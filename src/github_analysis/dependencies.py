from github_analysis.services.github import GitHubService
from github_analysis.config import settings

def get_github_service() -> GitHubService:
    """Dependency to provide GitHubService"""
    return GitHubService(settings.GITHUB_TOKEN)