from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True)
    github_id = Column(Integer, unique=True, nullable=False)  # Need this to avoid duplicates
    number = Column(Integer, nullable=False)  # Needed for GitHub API calls
    title = Column(String, nullable=False)  # Important for context
    body = Column(String)  # Important for context
    created_at = Column(DateTime, nullable=False)  # Useful for temporal analysis

    # Relationships for what we really care about
    comments = relationship("PRComment", back_populates="pull_request")
    diffs = relationship("PRDiff", back_populates="pull_request")
    # We'll add AI summary fields later


class PRComment(Base):
    __tablename__ = "pr_comments"

    id = Column(Integer, primary_key=True)
    github_id = Column(Integer, unique=True, nullable=False)
    body = Column(String, nullable=False)  # The actual comment content we want to analyze
    user_login = Column(String, nullable=False)  # Might be useful for analysis context
    pr_id = Column(Integer, ForeignKey("pull_requests.id"), nullable=False)

    pull_request = relationship("PullRequest", back_populates="comments")


class PRDiff(Base):
    __tablename__ = "pr_diffs"

    id = Column(Integer, primary_key=True)
    file_path = Column(String, nullable=False)  # Which file was changed
    content = Column(String, nullable=False)  # The actual changes we want to analyze
    pr_id = Column(Integer, ForeignKey("pull_requests.id"), nullable=False)

    pull_request = relationship("PullRequest", back_populates="diffs")