"""Schema models for GitLab issues."""

from enum import Enum

from pydantic import BaseModel

from src.schemas.base import GitLabResponseBase, PaginatedResponse


class IssueType(str, Enum):
    """Types of GitLab issues.

    Attributes:
        ISSUE: Standard issue.
        INCIDENT: Incident issue type.
        TEST_CASE: Test case issue type.
        TASK: Task issue type.
    """

    ISSUE = "issue"
    INCIDENT = "incident"
    TEST_CASE = "test_case"
    TASK = "task"


class IssueSeverity(str, Enum):
    """Severity levels for GitLab issues.

    Attributes:
        UNKNOWN: Unknown severity.
        LOW: Low severity.
        MEDIUM: Medium severity.
        HIGH: High severity.
        CRITICAL: Critical severity.
    """

    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IssueState(str, Enum):
    """State of GitLab issues.

    Attributes:
        OPENED: Issue is open.
        CLOSED: Issue is closed.
        ALL: All issue states.
    """

    OPENED = "opened"
    CLOSED = "closed"
    ALL = "all"


class GitLabIssue(GitLabResponseBase):
    """Simplified response model for a GitLab issue.

    Attributes:
        id: The unique identifier of the issue.
        iid: The internal ID of the issue within the project.
        project_id: The ID of the project the issue belongs to.
        title: The title of the issue.
        description: The description of the issue.
        state: The state of the issue (opened or closed).
        web_url: The web URL of the issue.
        _links: Links related to the issue.
    """

    id: int
    iid: int
    project_id: int
    title: str
    description: str | None = None
    state: str
    web_url: str


class CreateIssueInput(BaseModel):
    project_path: str
    title: str
    description: str | None = None
    labels: list[str] | None = None


class GetIssueInput(BaseModel):
    """Input model for getting a specific issue from a GitLab repository.

    Attributes:
        project_path: The path of the project (e.g., 'namespace/project').
        issue_iid: The internal ID of the issue within the project.
    """

    project_path: str
    issue_iid: int


class DeleteIssueInput(BaseModel):
    """Input model for deleting an issue from a GitLab repository.

    Attributes:
        project_path: The path of the project (e.g., 'namespace/project').
        issue_iid: The internal ID of the issue within the project.
    """

    project_path: str
    issue_iid: int


class MoveIssueInput(BaseModel):
    """Input model for moving an issue to a different project.

    Attributes:
        project_path: The path of the source project.
        issue_iid: The internal ID of the issue within the project.
        to_project_id: The ID of the target project.
    """

    project_path: str
    issue_iid: int
    to_project_id: int


class CreateIssueCommentInput(BaseModel):
    """Input model for creating a comment on a GitLab issue.

    Attributes:
        project_path: The path of the project (e.g., 'namespace/project').
        issue_iid: The internal ID of the issue within the project.
        body: The content of the comment.
    """

    project_path: str
    issue_iid: int
    body: str


class ListIssueCommentsInput(BaseModel):
    """Input model for listing comments on a GitLab issue.

    Attributes:
        project_path: The path of the project (e.g., 'namespace/project').
        issue_iid: The internal ID of the issue within the project.
        page: The page number for pagination.
        per_page: The number of items per page.
    """

    project_path: str
    issue_iid: int
    page: int = 1
    per_page: int = 20


class ListIssuesInput(BaseModel):
    """Input model for listing issues in a GitLab project.

    Attributes:
        project_path: The path of the project (e.g., 'namespace/project').
        state: The state of the issues to filter (opened, closed, or all).
        confidential: Whether to filter confidential issues.
        page: The page number for pagination.
        per_page: The number of items per page.
    """

    project_path: str
    state: str | None = None
    confidential: bool | None = None
    page: int = 1
    per_page: int = 20


class GitLabIssueListResponse(PaginatedResponse[GitLabIssue]):
    """Paginated response model for a list of GitLab issues.

    Attributes:
        count: Total number of issues available.
        items: The list of issues returned.
    """

    pass
