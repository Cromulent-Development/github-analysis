from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class PRCommentSchema(BaseModel):
    id: int = Field(description="GitHub comment ID")
    body: str = Field(description="Comment content")
    created_at: datetime = Field(description="Comment creation timestamp")
    user_login: str = Field(description="GitHub username of commenter")


class PRDiffSchema(BaseModel):
    file_path: str = Field(description="Path to the modified file")
    content: str = Field(description="Diff content")


class PullRequestSchema(BaseModel):
    number: int = Field(description="PR number")
    title: str = Field(description="PR title")
    body: Optional[str] = Field(None, description="PR description")
    created_at: datetime = Field(description="PR creation timestamp")
    updated_at: datetime = Field(description="PR last update timestamp")
    state: str = Field(description="PR state (open/closed/merged)")
    user_login: str = Field(description="PR author's GitHub username")
    comments: List[PRCommentSchema] = Field(default_factory=list, description="List of PR comments")
    diffs: List[PRDiffSchema] = Field(default_factory=list, description="List of file diffs")


class PRListResponse(BaseModel):
    items: List[PullRequestSchema]
    total_count: int = Field(description="Total number of PRs")


class PRDetailResponse(PullRequestSchema):
    pass  # We might add additional fields specific to detailed view