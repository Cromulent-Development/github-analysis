import enum

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from .base import Base


class ChangeType(enum.Enum):
    ADD = "add"
    DELETE = "delete"
    MODIFY = "modify"
    RENAME = "rename"


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True)
    github_id = Column(BigInteger, unique=True, nullable=False)
    number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    body = Column(String)
    created_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    comments = relationship(
        "PRComment", back_populates="pull_request", cascade="all, delete-orphan"
    )
    diffs = relationship(
        "PRDiff", back_populates="pull_request", cascade="all, delete-orphan"
    )

    analysis = relationship("PRAnalysis", back_populates="pull_request", uselist=False)


class PRComment(Base):
    __tablename__ = "pr_comments"

    id = Column(Integer, primary_key=True)
    github_id = Column(BigInteger, unique=True, nullable=False)
    body = Column(String, nullable=False)
    user_login = Column(String, nullable=False)
    pr_id = Column(
        Integer, ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False
    )

    pull_request = relationship("PullRequest", back_populates="comments")


class PRDiff(Base):
    __tablename__ = "pr_diffs"

    id = Column(Integer, primary_key=True)
    file_path = Column(String, nullable=False)
    old_file_path = Column(String)  # For renames
    change_type = Column(Enum(ChangeType), nullable=False)
    pr_id = Column(
        Integer, ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False
    )

    pull_request = relationship("PullRequest", back_populates="diffs")
    hunks = relationship(
        "DiffHunk", back_populates="diff", cascade="all, delete-orphan"
    )


class DiffHunk(Base):
    __tablename__ = "diff_hunks"

    id = Column(Integer, primary_key=True)
    old_start = Column(Integer, nullable=False)
    old_lines = Column(Integer, nullable=False)
    new_start = Column(Integer, nullable=False)
    new_lines = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    diff_id = Column(
        Integer, ForeignKey("pr_diffs.id", ondelete="CASCADE"), nullable=False
    )

    diff = relationship("PRDiff", back_populates="hunks")


class PRAnalysis(Base):
    __tablename__ = "pr_analyses"

    id = Column(Integer, primary_key=True)
    pr_id = Column(
        Integer, ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False
    )
    embedding = Column(ARRAY(Float))  # Store the vector embedding
    summary = Column(String)  # Store the AI-generated summary
    analysis_metadata = Column(
        JSON
    )  # Store any additional structured data from AI analysis

    # Relationship back to PR
    pull_request = relationship("PullRequest", back_populates="analysis")
