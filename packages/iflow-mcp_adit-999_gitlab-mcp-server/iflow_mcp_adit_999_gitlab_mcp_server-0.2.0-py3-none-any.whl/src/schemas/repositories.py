from enum import Enum

from src.schemas.base import (
    BaseModel,
    BaseResponseList,
    GitLabResponseBase,
    PaginatedResponse,
    VisibilityLevel,
)


class CreateRepositoryInput(BaseModel):
    """Input model for creating a new GitLab repository.

    Attributes:
        name: The name of the repository (e.g., 'namespace/name').
        description: Optional description of the repository.
        visibility: The visibility level of the repository (private, internal, public).
        initialize_with_readme: Whether to initialize the repository with a README file.
    """

    name: str
    description: str | None = None
    visibility: VisibilityLevel = VisibilityLevel.PRIVATE
    initialize_with_readme: bool = False


class GitLabRepository(GitLabResponseBase):
    """Response model for a GitLab repository.

    Attributes:
        id: The unique identifier of the repository.
        name: The name of the repository.
        path: The path of the repository.
        description: Optional description of the repository.
        web_url: The web URL of the repository.
        default_branch: The default branch of the repository.
    """

    id: int
    name: str
    path: str
    description: str | None = None
    web_url: str
    default_branch: str | None = None


class TreeItemType(str, Enum):
    """Types of items in the repository tree.

    Attributes:
        BLOB: A file.
        TREE: A directory.
    """

    BLOB = "blob"
    TREE = "tree"


class ListRepositoryTreeInput(BaseModel):
    """Input model for listing files and directories in a repository.

    Attributes:
        project_path: The path of the project (e.g., 'namespace/project').
        path: The path inside the repository (defaults to repository root).
        ref: The name of the branch, tag, or commit.
        recursive: Whether to get the contents recursively.
        per_page: Number of items to list per page.
    """

    project_path: str
    ref: str | None = None
    recursive: bool = False
    per_page: int = 20


class RepositoryTreeItem(GitLabResponseBase):
    """Response model for an item in the repository tree.

    Attributes:
        id: SHA1 identifier of the tree item.
        name: The name of the item.
        type: The type of the item (blob for files, tree for directories).
        path: The path of the item within the repository.
        mode: File mode.
    """

    id: str
    name: str
    type: TreeItemType
    path: str
    mode: str


class RepositoryTreeResponse(BaseResponseList[RepositoryTreeItem]):
    """Response model for repository tree listing."""

    pass


class SearchProjectsInput(BaseModel):
    """Input model for searching GitLab projects.

    Attributes:
        search: The search query.
        page: The page number for pagination.
        per_page: The number of items per page.
    """

    search: str
    page: int = 1
    per_page: int = 20


class GitLabSearchResponse(PaginatedResponse[dict[str, str | int | bool | None]]):
    """Response model for GitLab project search results."""

    pass
