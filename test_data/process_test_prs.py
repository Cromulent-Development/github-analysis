"""Script to process test PRs with both embedding approaches.

This script:
1. Loads test PRs from JSON files
2. Processes them with both embedding approaches (AI summary and raw diff)
3. Stores them in Qdrant
4. Compares similarities to evaluate which approach better identifies related changes
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from qdrant_client import QdrantClient
from qdrant_client.http import models

from github_analysis.config import settings
from github_analysis.models.models import (
    PullRequest,
    PRComment,
    PRDiff,
    DiffHunk,
    ChangeType,
)
from github_analysis.services.embedding import EmbeddingType

# Vector size for text-embedding-3-small model
VECTOR_SIZE = 1536


async def load_test_pr(file_path: str) -> Dict:
    """Load test PR data from JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


async def store_test_pr(session: AsyncSession, pr_data: Dict) -> PullRequest:
    """Store test PR data in database."""
    # Check if PR already exists
    query = select(PullRequest).where(PullRequest.github_id == pr_data["github_id"])
    result = await session.execute(query)
    existing_pr = result.scalar_one_or_none()

    if existing_pr:
        return existing_pr

    # Create new PR if it doesn't exist
    pr = PullRequest(
        github_id=pr_data["github_id"],
        number=pr_data["number"],
        title=pr_data["title"],
        body=pr_data["body"],
        created_at=datetime.fromisoformat(pr_data["created_at"].replace("Z", "+00:00")),
    )
    session.add(pr)
    await session.flush()

    # Store comments
    for comment in pr_data["comments"]:
        pr_comment = PRComment(
            github_id=comment["github_id"],
            body=comment["body"],
            user_login=comment["user_login"],
            pr_id=pr.id,
        )
        session.add(pr_comment)

    # Store diffs
    for diff in pr_data["diffs"]:
        pr_diff = PRDiff(
            file_path=diff["file_path"],
            change_type=ChangeType(diff["change_type"]),
            pr_id=pr.id,
        )
        session.add(pr_diff)
        await session.flush()

        # Store hunks
        for hunk in diff["hunks"]:
            diff_hunk = DiffHunk(
                old_start=hunk["old_start"],
                old_lines=hunk["old_lines"],
                new_start=hunk["new_start"],
                new_lines=hunk["new_lines"],
                content=hunk["content"],
                diff_id=pr_diff.id,
            )
            session.add(diff_hunk)

    await session.commit()
    return pr


async def clear_data(session: AsyncSession, qdrant_client: QdrantClient):
    """Clear existing data from database and Qdrant."""
    print("\nClearing existing data...")

    # Clear database tables
    await session.execute(text("TRUNCATE TABLE pr_analyses CASCADE"))
    await session.execute(text("TRUNCATE TABLE pull_requests CASCADE"))
    await session.commit()

    # Recreate Qdrant collection
    try:
        qdrant_client.delete_collection(settings.QDRANT_COLLECTION_NAME)
    except Exception:
        pass  # Collection might not exist

    qdrant_client.create_collection(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=VECTOR_SIZE,
            distance=models.Distance.COSINE,
        ),
    )
    print("Data cleared successfully")


async def process_test_prs(fresh: bool = False):
    """Process test PRs with both embedding approaches."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Initialize services
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    qdrant_client = QdrantClient(settings.QDRANT_HOST, port=settings.QDRANT_PORT)

    async with async_session() as session:
        # Clear existing data if requested
        if fresh:
            await clear_data(session, qdrant_client)

        # Process each test PR
        print("\nProcessing test PRs...")
        test_pr_files = [f for f in os.listdir("test_data/prs") if f.endswith(".json")]

        # Store PRs to get their database IDs
        pr_ids = {}  # Map PR numbers to database IDs
        for pr_file in test_pr_files:
            pr_data = await load_test_pr(f"test_data/prs/{pr_file}")
            pr = await store_test_pr(session, pr_data)
            pr_ids[pr_data["number"]] = pr.id

        # First store both types of embeddings for each PR
        print("\nStoring embeddings for both approaches...")
        from github_analysis.services.analysis_service import AnalysisService
        from github_analysis.services.ai_service import AIService
        from github_analysis.services.embedding import EmbeddingService

        ai_service = AIService(api_key=settings.OPENAI_API_KEY)
        embedding_service = EmbeddingService(api_key=settings.OPENAI_API_KEY)
        analysis_service = AnalysisService(
            session, qdrant_client, ai_service, embedding_service
        )

        for pr_file in test_pr_files:
            pr_data = await load_test_pr(f"test_data/prs/{pr_file}")
            pr_number = pr_data["number"]
            print(f"\nProcessing PR #{pr_number}")

            # Store both types of embeddings
            for embedding_type in [EmbeddingType.AI_SUMMARY, EmbeddingType.RAW_DIFF]:
                print(f"Storing {embedding_type.value} embedding...")
                try:
                    await analysis_service.process_pr(pr_number, embedding_type)
                except Exception as e:
                    print(
                        f"Error storing {embedding_type.value} embedding "
                        f"for PR {pr_number}: {e}"
                    )
                    continue

        # Now compare similarities with both approaches
        print("\nComparing similarities...")
        for embedding_type in [EmbeddingType.AI_SUMMARY, EmbeddingType.RAW_DIFF]:
            print(f"\nTesting {embedding_type.value} approach:")

            # For each PR, find similar PRs
            for pr_file in test_pr_files:
                pr_data = await load_test_pr(f"test_data/prs/{pr_file}")
                pr_number = pr_data["number"]
                pr_id = pr_ids[pr_number]

                # Get PR's embedding from Qdrant
                try:
                    print(f"\nTrying to get embedding for PR #{pr_number}")
                    # Use even numbers for AI_SUMMARY, odd for RAW_DIFF
                    point_id = pr_number * 2 + (
                        0 if embedding_type == EmbeddingType.AI_SUMMARY else 1
                    )
                    points = qdrant_client.retrieve(
                        collection_name=settings.QDRANT_COLLECTION_NAME,
                        ids=[point_id],
                        with_vectors=True,
                    )
                    if not points:
                        print(f"No points found for PR {pr_number} (DB ID: {pr_id})")
                        continue
                    pr_point = points[0]
                    print(f"Found point with payload: {pr_point.payload}")
                except Exception as e:
                    print(f"Error getting embedding for PR {pr_number}: {e}")
                    continue

                # Log detailed Qdrant collection state
                collection_info = qdrant_client.get_collection(
                    settings.QDRANT_COLLECTION_NAME
                )
                print("\nQdrant collection info:")
                print(f"  Points count: {collection_info.points_count}")
                print(f"  Vectors config: {collection_info.config.params}")

                # List all points in collection
                scroll_response = qdrant_client.scroll(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    limit=100,
                    with_payload=True,
                    with_vectors=False,
                )
                points = scroll_response[0]
                print("\nPoints in collection:")
                for point in points:
                    print(f"  ID: {point.id}")
                    print(f"  Embedding type: {point.payload.get('embedding_type')}")
                    print(f"  PR number: {point.payload.get('context', {}).get('id')}")
                    print("  ---")

                # Search for similar PRs using the PR's embedding
                try:
                    print(f"Searching for similar PRs to #{pr_number}")
                    similar_prs = qdrant_client.search(
                        collection_name=settings.QDRANT_COLLECTION_NAME,
                        query_vector=list(pr_point.vector),
                        query_filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="embedding_type",
                                    match=models.MatchValue(value=embedding_type.value),
                                ),
                            ],
                            must_not=[
                                models.FieldCondition(
                                    key="context.id",
                                    match=models.MatchValue(value=pr_number),
                                ),
                            ],
                        ),
                        limit=2,
                    )
                    print(f"Found {len(similar_prs)} similar PRs")
                except Exception as e:
                    print(f"Error searching for similar PRs: {e}")
                    continue

                print(f"\n{'-'*50}")
                print(f"Similar PRs to #{pr_number}: {pr_data['title']}")
                print(f"Using {embedding_type.value} approach:")
                for point in similar_prs:
                    similarity = point.score if hasattr(point, "score") else 0
                    similar_pr_id = point.payload["context"]["id"]
                    similar_pr_title = point.payload["context"]["title"]
                    print(
                        f"  - #{similar_pr_id}: {similar_pr_title}\n"
                        f"    Similarity: {similarity:.3f}"
                    )


def print_usage():
    print(
        """
Usage: python process_test_prs.py [--fresh]

Options:
  --fresh  Clear existing data before processing

Before running, ensure your .env file has:
- OPENAI_API_KEY
- Database settings (or use defaults)
- Qdrant settings (or use defaults)

The script will:
1. Load test PRs from test_data/prs/*.json
2. Process them with both embedding approaches
3. Compare similarities to evaluate which approach works better
"""
    )


if __name__ == "__main__":
    import sys

    fresh = "--fresh" in sys.argv
    if fresh:
        print("\nStarting fresh - clearing existing data...")
    asyncio.run(process_test_prs(fresh))
