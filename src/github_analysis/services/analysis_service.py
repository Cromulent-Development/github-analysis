import logging
from typing import Dict, Tuple
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from github_analysis.models.models import PullRequest, PRAnalysis, PRDiff
from github_analysis.services.ai_service import AIService
from github_analysis.services.embedding import EmbeddingService, EmbeddingType


class AnalysisService:
    def __init__(
        self,
        db: AsyncSession,
        qdrant_client: QdrantClient,
        ai_service: AIService,
        embedding_service: EmbeddingService,
    ):
        self.db = db
        self.qdrant = qdrant_client
        self.ai = ai_service
        self.embedding_service = embedding_service

        try:
            self.qdrant.get_collection("github_changes")
        except Exception:
            self.qdrant.create_collection(
                collection_name="github_changes",
                vectors_config=models.VectorParams(
                    size=1536,
                    distance=models.Distance.COSINE,
                ),
            )

    async def get_pr_context(self, pr_id: int) -> Tuple[Dict, int]:
        """Get all PR data and its database ID"""
        query = (
            select(PullRequest)
            .where(PullRequest.number == pr_id)
            .options(
                joinedload(PullRequest.diffs).joinedload(PRDiff.hunks),
                joinedload(PullRequest.comments),
            )
        )

        result = await self.db.execute(query)
        pr = result.unique().scalar_one_or_none()

        if not pr:
            raise ValueError(f"PR number {pr_id} not found")

        diff_context = []
        for diff in pr.diffs:
            diff_context.append(
                {
                    "file": diff.file_path,
                    "change_type": diff.change_type.value,
                    "changes": [hunk.content for hunk in diff.hunks],
                }
            )

        # Create comments_context from PR comments
        comments_context = [
            {"author": c.user_login, "comment": c.body} for c in pr.comments
        ]

        return {
            "id": pr.number,
            "title": pr.title,
            "description": pr.body,
            "changes": diff_context,
            "discussion": comments_context,
        }, pr.id

    async def process_pr(
        self, pr_id: int, embedding_type: EmbeddingType = EmbeddingType.AI_SUMMARY
    ):
        pr_context, db_id = await self.get_pr_context(pr_id)

        if embedding_type == EmbeddingType.AI_SUMMARY:
            try:
                # Get AI analysis first
                content = await self.ai.analyze_pr(pr_context)
                metadata = content  # Full AI analysis as metadata
                summary = content.get("summary")
            except Exception as e:
                logging.error(f"Failed to get AI analysis for PR {pr_id}: {e}")
                # Fall back to raw diff for AI_SUMMARY if analysis fails
                content = {"changes": pr_context["changes"]}
                metadata = {"raw_diff": True, "changes": pr_context["changes"]}
                summary = None
            point_id = pr_id * 2  # Even numbers for AI_SUMMARY
        else:
            # Use raw diff content
            content = {"changes": pr_context["changes"]}
            metadata = {"raw_diff": True, "changes": pr_context["changes"]}
            summary = None
            point_id = pr_id * 2 + 1  # Odd numbers for RAW_DIFF

        text_for_embedding = self.embedding_service.prepare_text_for_embedding(
            content, embedding_type
        )
        embeddings = await self.embedding_service.create_embedding(text_for_embedding)

        # Store embedding in Qdrant
        logging.info(f"Storing embedding for PR {pr_id} in Qdrant")
        try:
            self.qdrant.upsert(
                collection_name="github_changes",
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=embeddings,
                        payload={
                            "context": pr_context,
                            "content": metadata,
                            "embedding_type": embedding_type.value,
                        },
                    )
                ],
            )

            # Verify point was stored
            stored_point = self.qdrant.retrieve(
                collection_name="github_changes",
                ids=[point_id],
            )
            if not stored_point:
                logging.error(f"Failed to verify storage of PR {pr_id} in Qdrant")
                raise Exception(f"Failed to verify storage of PR {pr_id} in Qdrant")
            logging.info(f"Successfully verified storage of PR {pr_id} in Qdrant")

        except Exception as e:
            logging.error(f"Failed to store PR {pr_id} in Qdrant: {str(e)}")
            raise

        analysis = PRAnalysis(
            pr_id=db_id,
            embedding=embeddings,
            summary=summary,
            analysis_metadata=metadata,
        )
        self.db.add(analysis)
        await self.db.commit()

        return {
            "pr_id": pr_id,
            "content": metadata,
            "embedding_type": embedding_type.value,
            "stored": True,
        }
