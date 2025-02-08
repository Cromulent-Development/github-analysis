from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True)
    github_id = Column(Integer, unique=True, nullable=False)
    number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    body = Column(String)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    state = Column(String, nullable=False)
    user_login = Column(String, nullable=False)

    comments = relationship("PRComment", back_populates="pull_request")
    diffs = relationship("PRDiff", back_populates="pull_request")


class PRComment(Base):
    __tablename__ = "pr_comments"

    id = Column(Integer, primary_key=True)
    github_id = Column(Integer, unique=True, nullable=False)
    body = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    user_login = Column(String, nullable=False)
    pr_id = Column(Integer, ForeignKey("pull_requests.id"), nullable=False)

    pull_request = relationship("PullRequest", back_populates="comments")


class PRDiff(Base):
    __tablename__ = "pr_diffs"

    id = Column(Integer, primary_key=True)
    file_path = Column(String, nullable=False)
    content = Column(String, nullable=False)
    pr_id = Column(Integer, ForeignKey("pull_requests.id"), nullable=False)

    pull_request = relationship("PullRequest", back_populates="diffs")