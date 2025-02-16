"""Script to compare embedding approaches using sample PR data."""

import json
import os
from typing import Dict

from github_analysis.services.ai_service import AIService
from github_analysis.services.embedding import EmbeddingService, EmbeddingType


def load_test_pr(file_path: str) -> Dict:
    """Load test PR data from JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def prepare_pr_context(pr_data: Dict) -> Dict:
    """Convert PR data into the format expected by our services."""
    diff_context = []
    for diff in pr_data["diffs"]:
        diff_context.append(
            {
                "file": diff["file_path"],
                "change_type": diff["change_type"],
                "changes": [hunk["content"] for hunk in diff["hunks"]],
            }
        )

    return {
        "id": pr_data["number"],
        "title": pr_data["title"],
        "description": pr_data["body"],
        "changes": diff_context,
        "discussion": [
            {"author": c["user_login"], "comment": c["body"]}
            for c in pr_data["comments"]
        ],
    }


async def compare_embeddings(openai_key: str):
    """Compare embedding approaches using sample PRs."""
    ai_service = AIService(api_key=openai_key)
    embedding_service = EmbeddingService(api_key=openai_key)

    test_prs = []
    for pr_file in os.listdir("test_data/prs"):
        if pr_file.endswith(".json"):
            pr_data = load_test_pr(f"test_data/prs/{pr_file}")
            test_prs.append(prepare_pr_context(pr_data))

    results = {EmbeddingType.AI_SUMMARY: [], EmbeddingType.RAW_DIFF: []}

    for pr in test_prs:
        print(f"\nProcessing PR {pr['id']}: {pr['title']}")

        # Get embeddings using AI summary approach
        print("\nAI Summary approach:")
        ai_content = await ai_service.analyze_pr(pr)
        ai_text = embedding_service.prepare_text_for_embedding(
            ai_content, EmbeddingType.AI_SUMMARY
        )
        ai_embedding = await embedding_service.create_embedding(ai_text)
        results[EmbeddingType.AI_SUMMARY].append(
            {"pr": pr, "embedding": ai_embedding, "text": ai_text}
        )
        print(f"Generated summary: {ai_content.get('summary')}")

        # Get embeddings using raw diff approach
        print("\nRaw Diff approach:")
        diff_content = {"changes": pr["changes"]}
        diff_text = embedding_service.prepare_text_for_embedding(
            diff_content, EmbeddingType.RAW_DIFF
        )
        diff_embedding = await embedding_service.create_embedding(diff_text)
        results[EmbeddingType.RAW_DIFF].append(
            {"pr": pr, "embedding": diff_embedding, "text": diff_text}
        )
        print(f"Processed {len(pr['changes'])} file changes")

    # Compare similarities within each approach
    for approach, prs in results.items():
        print(f"\n{approach.value} Approach Results:")
        for i, pr1 in enumerate(prs):
            for pr2 in prs[i + 1 :]:
                # Calculate cosine similarity
                similarity = sum(
                    a * b for a, b in zip(pr1["embedding"], pr2["embedding"])
                ) / (
                    (
                        sum(a * a for a in pr1["embedding"])
                        * sum(b * b for b in pr2["embedding"])
                    )
                    ** 0.5
                )
                print(
                    f"\nSimilarity between PR {pr1['pr']['id']} and "
                    f"PR {pr2['pr']['id']}: {similarity:.3f}"
                )
                print(f"PR {pr1['pr']['id']}: {pr1['pr']['title']}")
                print(f"PR {pr2['pr']['id']}: {pr2['pr']['title']}")


if __name__ == "__main__":
    import asyncio
    import sys

    if len(sys.argv) != 2:
        print("Usage: python compare_embeddings.py OPENAI_API_KEY")
        sys.exit(1)

    asyncio.run(compare_embeddings(sys.argv[1]))
