from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import Base


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True)
    github_id = Column(BigInteger, unique=True, nullable=False)  # Avoid duplicates, supports large IDs
    number = Column(Integer, nullable=False)  # PR number from GitHub
    title = Column(String, nullable=False)  # Title of the PR
    body = Column(String)  # Body/description of the PR
    created_at = Column(DateTime(timezone=True), nullable=False)  # Supports timezone-aware datetimes

    # Relationships
    comments = relationship("PRComment", back_populates="pull_request", cascade="all, delete-orphan")
    diffs = relationship("PRDiff", back_populates="pull_request", cascade="all, delete-orphan")


class PRComment(Base):
    __tablename__ = "pr_comments"

    id = Column(Integer, primary_key=True)
    github_id = Column(BigInteger, unique=True, nullable=False)
    body = Column(String, nullable=False)  # Comment content
    user_login = Column(String, nullable=False)  # User who posted the comment
    pr_id = Column(Integer, ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False)

    pull_request = relationship("PullRequest", back_populates="comments")


class PRDiff(Base):
    __tablename__ = "pr_diffs"

    id = Column(Integer, primary_key=True)
    file_path = Column(String, nullable=False)  # File path of the diff
    content = Column(String, nullable=False)  # Content of the diff
    pr_id = Column(Integer, ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False)

    pull_request = relationship("PullRequest", back_populates="diffs")
