from datetime import datetime
from typing import List
import aiohttp
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from github_analysis.models.models import PRDiff, PRComment, PullRequest


class GitHubService:
    def __init__(self, db: AsyncSession, access_token: str, base_url: str = "https://api.github.com"):
        self.db = db
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }

    async def _get_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "all",
        page: int = 1,
        per_page: int = 30
    ) -> List[dict]:
        """Fetch pull requests from GitHub API."""
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

    async def _get_pr_comments(self, owner: str, repo: str, pr_number: int) -> List[dict]:
        """Fetch comments for a specific PR from GitHub API."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments"

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail="Failed to fetch PR comments"
                    )
                return await response.json()

    async def _get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
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

    async def store_pr(self, owner: str, repo: str, pr_data: dict) -> dict:
        pr_number = pr_data["number"]

        try:
            comments = await self._get_pr_comments(owner, repo, pr_number)
            diff = await self._get_pr_diff(owner, repo, pr_number)
        except Exception as fetch_exc:
            return {
                "status": "error",
                "pr_number": pr_number,
                "detail": f"External fetch error: {fetch_exc}"
            }

        try:
            async with self.db.begin():
                pr = PullRequest(
                    github_id=pr_data["id"],
                    number=pr_number,
                    title=pr_data["title"],
                    body=pr_data.get("body", ""),
                    created_at=datetime.fromisoformat(pr_data["created_at"].replace("Z", "+00:00"))
                )
                self.db.add(pr)
                await self.db.flush()

                for comment_data in comments:
                    comment = PRComment(
                        github_id=comment_data["id"],
                        body=comment_data["body"],
                        user_login=comment_data["user"]["login"],
                        pr_id=pr.id
                    )
                    self.db.add(comment)

                diff_record = PRDiff(
                    file_path="full_diff",
                    content=diff,
                    pr_id=pr.id
                )
                self.db.add(diff_record)
            return {"status": "success", "pr_number": pr_number}

        except IntegrityError:
            return {"status": "duplicate", "pr_number": pr_number}

        except Exception as db_exc:
            return {
                "status": "error",
                "pr_number": pr_number,
                "detail": f"Database error: {db_exc}"
            }

    async def fetch_and_store_prs(self, owner: str, repo: str, limit: int = 30) -> dict:
        """Fetch PRs from GitHub and store them in the database."""
        prs_data = await self._get_pull_requests(owner, repo, per_page=limit)
        results = {
            "stored": [],
            "duplicates": [],
            "errors": [],
            "total_processed": len(prs_data)
        }

        for pr_data in prs_data:
            result = await self.store_pr(owner, repo, pr_data)
            if result["status"] == "success":
                results["stored"].append(result["pr_number"])
            elif result["status"] == "duplicate":
                results["duplicates"].append(result["pr_number"])
            else:
                results["errors"].append({
                    "pr_number": result["pr_number"],
                    "detail": result.get("detail")
                })

        return results
