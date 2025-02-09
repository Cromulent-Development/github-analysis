from typing import Dict, List
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sqlalchemy.ext.asyncio import AsyncSession
from github_analysis.models.models import PullRequest, PRAnalysis
from github_analysis.services.ai_service import AIService


class AnalysisService:
    def __init__(
        self, db: AsyncSession, qdrant_client: QdrantClient, ai_service: AIService
    ):
        self.db = db
        self.qdrant = qdrant_client
        self.ai = ai_service

    async def get_pr_context(self, pr_id: int) -> Dict:
        """Get all PR data in a format ready for AI analysis"""
        async with self.db.begin():
            pr = await self.db.get(PullRequest, pr_id)
            if not pr:
                raise ValueError(f"PR {pr_id} not found")

            # Get all the context in a clean format
            diff_context = []
            for diff in pr.diffs:
                diff_context.append(
                    {
                        "file": diff.file_path,
                        "change_type": diff.change_type.value,
                        "changes": [hunk.content for hunk in diff.hunks],
                    }
                )

            comments_context = [
                {"author": c.user_login, "comment": c.body} for c in pr.comments
            ]

            return {
                "id": pr.id,
                "title": pr.title,
                "description": pr.body,
                "changes": diff_context,
                "discussion": comments_context,
            }

    async def process_pr(self, pr_id: int):
        """Full pipeline to process a PR"""
        # Get the raw context
        pr_context = await self.get_pr_context(pr_id)

        # Get AI analysis
        ai_analysis = await self.ai.analyze_pr(pr_context)

        # Generate embeddings from AI analysis
        embeddings = await self.ai.create_embeddings(ai_analysis)

        # Store in vector DB
        self.qdrant.upsert(
            collection_name="github_changes",
            points=[
                models.PointStruct(
                    id=pr_id,
                    vector=embeddings,
                    payload={"context": pr_context, "analysis": ai_analysis},
                )
            ],
        )

        # Store analysis in postgres too
        analysis = PRAnalysis(
            pr_id=pr_id,
            embedding=embeddings,
            summary=ai_analysis.get("summary"),
            metadata=ai_analysis,
        )
        self.db.add(analysis)
        await self.db.commit()

        return {"pr_id": pr_id, "analysis": ai_analysis, "stored": True}
