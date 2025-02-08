from typing import List, Optional
import aiohttp
from fastapi import HTTPException


class GitHubService:
    def __init__(self, access_token: str, base_url: str = "https://api.github.com"):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }

    async def get_pull_requests(
            self,
            owner: str,
            repo: str,
            state: str = "all",
            page: int = 1,
            per_page: int = 30
    ) -> List[dict]:
        """Fetch pull requests for a given repository."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        params = {"state": state, "page": page, "per_page": per_page}

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url, params=params) as response:
                if response.status == 404:
                    raise HTTPException(status_code=404, detail="Repository not found")
                elif response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail="Failed to fetch pull requests"
                    )
                return await response.json()

    async def get_pr_comments(self, owner: str, repo: str, pr_number: int) -> List[dict]:
        """Fetch comments for a specific pull request."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments"

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail="Failed to fetch PR comments"
                    )
                return await response.json()

    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """Fetch the diff for a specific pull request."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail="Failed to fetch PR diff"
                    )
                return await response.text()