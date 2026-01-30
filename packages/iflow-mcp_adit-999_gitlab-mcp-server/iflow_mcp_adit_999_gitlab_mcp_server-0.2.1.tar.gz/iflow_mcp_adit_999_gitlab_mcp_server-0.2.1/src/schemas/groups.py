from enum import Enum

from pydantic import BaseModel

from src.schemas.base import GitLabResponseBase, PaginatedResponse, VisibilityLevel


class GroupAccessLevel(int, Enum):
    """GitLab group access levels.

    Attributes:
        NO_ACCESS: No access.
        MINIMAL_ACCESS: Minimal access - only view.
        GUEST: Guest access.
        REPORTER: Reporter access.
        DEVELOPER: Developer access.
        MAINTAINER: Maintainer access.
        OWNER: Owner access.
    """

    NO_ACCESS = 0
    MINIMAL_ACCESS = 5
    GUEST = 10
    REPORTER = 20
    DEVELOPER = 30
    MAINTAINER = 40
    OWNER = 50


class GitLabGroup(GitLabResponseBase):
    """Response model for a GitLab group.

    Attributes:
        id: The unique identifier of the group.
        name: The name of the group.
        path: The path of the group.
        description: Optional description of the group.
        visibility: The visibility level of the group.
        web_url: The web URL of the group.
        parent_id: The ID of the parent group, if any.
    """

    id: int
    name: str
    path: str
    description: str | None = None
    visibility: VisibilityLevel
    web_url: str
    parent_id: int | None = None


class ListGroupsInput(BaseModel):
    """Input model for listing GitLab groups.

    Attributes:
        search: Optional search query to filter groups by name.
        owned: Whether to only include groups owned by the current user.
        min_access_level: Minimum access level required.
        top_level_only: Whether to only include top-level groups.
        page: The page number for pagination.
        per_page: The number of items per page.
    """

    search: str | None = None
    owned: bool = False
    min_access_level: GroupAccessLevel | None = None
    top_level_only: bool = False
    page: int = 1
    per_page: int = 20


class GitLabGroupListResponse(PaginatedResponse[GitLabGroup]):
    """Response model for listing GitLab groups."""

    pass


class GetGroupInput(BaseModel):
    """Input model for getting a specific GitLab group.

    Attributes:
        group_id: The ID or path of the group.
    """

    group_id: str


class CreateGroupInput(BaseModel):
    """Input model for creating a new GitLab group.

    Attributes:
        name: The name of the group.
        path: The path of the group.
        description: Optional description of the group.
        visibility: The visibility level of the group.
        parent_id: Optional ID of the parent group.
        auto_devops_enabled: Whether Auto DevOps is enabled for the group.
    """

    name: str
    path: str
    description: str | None = None
    visibility: VisibilityLevel = VisibilityLevel.PRIVATE
    parent_id: int | None = None
    auto_devops_enabled: bool = False


class UpdateGroupInput(BaseModel):
    """Input model for updating a GitLab group.

    Attributes:
        group_id: The ID or path of the group.
        name: Optional new name for the group.
        path: Optional new path for the group.
        description: Optional new description for the group.
        visibility: Optional new visibility level for the group.
    """

    group_id: str
    name: str | None = None
    path: str | None = None
    description: str | None = None
    visibility: VisibilityLevel | None = None


class DeleteGroupInput(BaseModel):
    """Input model for deleting a GitLab group.

    Attributes:
        group_id: The ID or path of the group.
    """

    group_id: str


class GetGroupByProjectNamespaceInput(BaseModel):
    """Input model for getting a GitLab group based on a project namespace.

    Attributes:
        project_namespace: The namespace path of the project.
    """

    project_namespace: str
