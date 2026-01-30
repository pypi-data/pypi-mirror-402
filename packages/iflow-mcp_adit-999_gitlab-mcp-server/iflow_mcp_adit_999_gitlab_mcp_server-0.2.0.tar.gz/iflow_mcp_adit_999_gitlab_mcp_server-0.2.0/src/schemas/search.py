"""Search schemas for GitLab search API.

This module defines Pydantic models for GitLab search functionality.
"""

from enum import Enum
from typing import ClassVar

from pydantic import BaseModel, Field, field_validator


class SearchScope(str, Enum):
    """Enumeration of valid search scopes in GitLab."""

    PROJECTS = "projects"
    BLOBS = "blobs"
    WIKI_BLOBS = "wiki_blobs"
    COMMITS = "commits"
    ISSUES = "issues"
    MERGE_REQUESTS = "merge_requests"
    MILESTONES = "milestones"
    NOTES = "notes"


class BlobSearchFilters(BaseModel):
    """Filters for blob search (Premium/Ultimate tier only)."""

    filename: str | None = None
    path: str | None = None
    extension: str | None = None


class SearchRequest(BaseModel):
    """Base search request model for GitLab API."""

    MIN_SEARCH_LENGTH: ClassVar[int] = 3
    scope: SearchScope = Field(
        ..., description="The scope to search in. Determines the type of results."
    )
    search: str = Field(
        ..., description="The search query to use. Must be at least 3 characters."
    )

    @field_validator("search")
    @classmethod
    def validate_search_length(cls, v: str) -> str:
        if len(v) < cls.MIN_SEARCH_LENGTH:
            raise ValueError(
                f"Search query must be at least {cls.MIN_SEARCH_LENGTH} characters"
            )
        return v


class GlobalSearchRequest(SearchRequest):
    """Search request for global GitLab search."""

    pass


class GroupSearchRequest(SearchRequest):
    """Search request for group-specific search."""

    group_id: str = Field(..., description="The ID or URL-encoded path of the group")


class ProjectSearchRequest(SearchRequest):
    """Search request for project-specific search."""

    project_id: str = Field(
        ..., description="The ID or URL-encoded path of the project"
    )
    ref: str | None = Field(
        None, description="The branch or tag to search in (for blobs/commits)"
    )


class SearchResult(BaseModel):
    """Base class for search results."""

    pass


class ProjectSearchResult(SearchResult):
    """Project search result model."""

    id: int
    name: str
    description: str | None = None
    name_with_namespace: str
    path: str
    path_with_namespace: str
    created_at: str
    default_branch: str
    topics: list[str] = []
    ssh_url_to_repo: str
    http_url_to_repo: str
    web_url: str
    readme_url: str | None = None
    avatar_url: str | None = None
    star_count: int
    forks_count: int
    last_activity_at: str


class BlobSearchResult(SearchResult):
    """Blob search result model for file content."""

    basename: str
    data: str
    path: str
    filename: str
    id: str | None = None
    ref: str
    startline: int
    project_id: int


class SearchResponse(BaseModel):
    """Generic search response containing only project and blob results."""

    projects: list[ProjectSearchResult] = []
    blobs: list[BlobSearchResult] = []
    wiki_blobs: list[BlobSearchResult] = []
