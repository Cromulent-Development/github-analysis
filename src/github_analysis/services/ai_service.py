import json
from typing import Dict, List
import openai
from openai import AsyncOpenAI
from openai.types import ResponseFormatJSONObject
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat.completion_create_params import ResponseFormat


class AIService:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    def _format_changes_for_prompt(self, changes: List[Dict]) -> str:
        """Format code changes in a readable way for the AI"""
        formatted = []
        for change in changes:
            formatted.append(f"File: {change['file']} ({change['change_type']})")
            for chunk in change["changes"]:
                formatted.append(chunk.strip())
            formatted.append("")  # Empty line between files
        return "\n".join(formatted)

    def _format_discussion_for_prompt(self, comments: List[Dict]) -> str:
        """Format PR comments/discussion for the AI"""
        if not comments:
            return "No discussion."
        return "\n".join(f"{c['author']}: {c['comment']}" for c in comments)

    def _create_analysis_prompt(self, pr_context: Dict) -> str:
        """Create a detailed prompt for the AI"""
        changes = self._format_changes_for_prompt(pr_context["changes"])
        discussion = self._format_discussion_for_prompt(pr_context["discussion"])

        return f"""Analyze this pull request and provide a structured summary of the changes.

Title: {pr_context['title']}

Description:
{pr_context['description'] or 'No description provided.'}

Changes:
{changes}

Discussion:
{discussion}

Provide an analysis with the following:
1. A concise summary of what this PR accomplishes
2. The technical nature of the changes (e.g., bug fix, feature addition, refactor, etc.)
3. The impact and scope of the changes
4. Any notable patterns or concerns in the implementation
5. Key points from the discussion/comments, if relevant

Format the response as a JSON object with these keys:
- summary: A paragraph summarizing the changes
- change_type: List of categories (e.g., ["bug-fix", "documentation", "feature"])
- impact_level: One of "low", "medium", "high"
- impact_details: Explanation of the impact
- key_points: List of important observations
- technical_details: Technical aspects of the implementation"""

    async def analyze_pr(self, pr_context: Dict) -> Dict:
        """Get AI analysis of the PR"""
        prompt = self._create_analysis_prompt(pr_context)
        messages = [
            {
                "role": "system",
                "content": "You are an expert code reviewer and software engineer. Analyze pull requests and provide structured insights about code changes.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        try:
            if response.choices[0].message.content is None:
                raise ValueError("No content in response")
            analysis = json.loads(response.choices[0].message.content)
            return analysis
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response: {e}")

    async def create_embeddings(self, analysis: Dict) -> List[float]:
        """Create embeddings from the AI analysis"""
        # Combine relevant fields into a single text for embedding
        text_to_embed = f"{analysis['summary']} {analysis['impact_details']} {' '.join(analysis['key_points'])}"

        response = await self.client.embeddings.create(
            model="text-embedding-3-small", input=text_to_embed
        )

        return response.data[0].embedding
