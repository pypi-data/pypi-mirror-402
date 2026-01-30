"""Pydantic schemas for GitLab commit data structures."""

from src.schemas.base import GitLabResponseBase


class GitLabCommitDetail(GitLabResponseBase):
    """Response model for GitLab commit details.

    Attributes:
        id: Full commit SHA.
        short_id: Shortened commit SHA.
        title: Commit title.
        message: Full commit message.
        created_at: Date the commit was created.
        stats: Commit statistics (additions, deletions).
    """

    id: str
    short_id: str
    title: str
    message: str
    created_at: str
