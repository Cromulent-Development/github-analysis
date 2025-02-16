# services/embedding_service.py
from enum import Enum
from typing import List, Dict
from openai import AsyncOpenAI


class EmbeddingType(Enum):
    AI_SUMMARY = "ai_summary"
    RAW_DIFF = "raw_diff"


class EmbeddingService:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def create_embedding(self, text: str) -> List[float]:
        """Create embedding from any text content"""
        response = await self.client.embeddings.create(
            model="text-embedding-3-small", input=text
        )
        return response.data[0].embedding

    def prepare_text_for_embedding(
        self, content: Dict, embedding_type: EmbeddingType
    ) -> str:
        """Prepare the text that will be embedded based on the type"""
        if embedding_type == EmbeddingType.AI_SUMMARY:
            return f"{content['summary']} {content['impact_details']} {' '.join(content['key_points'])}"
        else:
            # For raw diffs, combine all changes into single text
            changes = []
            for change in content["changes"]:
                changes.append(f"File: {change['file']} ({change['change_type']})")
                changes.extend(change["changes"])
            return "\n".join(changes)
