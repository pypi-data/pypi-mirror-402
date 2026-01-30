"""Pydantic schemas for GitLab branch operations."""

from enum import Enum

from pydantic import BaseModel, Field, HttpUrl

from src.schemas.base import BaseResponseList, GitLabResponseBase
from src.schemas.commits import GitLabCommitDetail


class AccessLevel(int, Enum):
    """GitLab access level permission values.

    Attributes:
        NO_ACCESS: No access (0).
        DEVELOPER: Developer access (30).
        MAINTAINER: Maintainer access (40).
        ADMIN: Admin access (60).
    """

    NO_ACCESS = 0
    DEVELOPER = 30
    MAINTAINER = 40
    ADMIN = 60


class CreateBranchInput(BaseModel):
    """Input model for creating a new branch in a GitLab repository.

    Attributes:
        project_path: The path of the project (e.g., 'namespace/project').
        branch_name: The name of the branch to create.
        ref: The reference (branch, tag, or commit) to create the branch from.
    """

    project_path: str
    branch_name: str
    ref: str


class GitLabReference(GitLabResponseBase):
    """Response model for a GitLab branch or reference.

    Attributes:
        name: The name of the branch or reference.
        commit: Details about the commit the reference points to.
        merged: Whether the branch is merged.
        protected: Whether the branch is protected.
        default: Whether this is the default branch.
        developers_can_push: Whether developers have push access.
        developers_can_merge: Whether developers have merge access.
        can_push: Whether the current user can push to this branch.
        web_url: URL to view the branch in the GitLab web interface.
    """

    name: str
    commit: GitLabCommitDetail = Field(...)
    merged: bool = False
    protected: bool = False
    default: bool = False
    developers_can_push: bool = False
    developers_can_merge: bool = False
    can_push: bool = True
    web_url: HttpUrl | None = None


class GitLabBranchList(BaseResponseList[GitLabReference]):
    """Response model for a list of GitLab branches."""

    pass


class GetDefaultBranchRefInput(BaseModel):
    """Input model for getting the default branch of a GitLab repository.

    Attributes:
        project_path: The path of the project (e.g., 'namespace/project').
    """

    project_path: str


class ListBranchesInput(BaseModel):
    """Input model for listing branches in a GitLab repository.

    Attributes:
        project_path: The path of the project (e.g., 'namespace/project').
        search: Optional search pattern for branch names.
    """

    project_path: str
    search: str | None = None


class DeleteBranchInput(BaseModel):
    """Input model for deleting a branch from a GitLab repository.

    Attributes:
        project_path: The path of the project (e.g., 'namespace/project').
        branch_name: The name of the branch to delete.
    """

    project_path: str
    branch_name: str


class GetBranchInput(BaseModel):
    """Input model for getting a single branch from a GitLab repository.

    Attributes:
        project_path: The path of the project (e.g., 'namespace/project').
        branch_name: The name of the branch to retrieve.
    """

    project_path: str
    branch_name: str


class DeleteMergedBranchesInput(BaseModel):
    """Input model for deleting all merged branches in a GitLab repository.

    Attributes:
        project_path: The path of the project (e.g., 'namespace/project').
    """

    project_path: str


class AccessLevelModel(BaseModel):
    """Model for specifying an access level for branch protection.

    Attributes:
        access_level: The access level value (from AccessLevel enum).
    """

    access_level: AccessLevel


class ProtectBranchInput(BaseModel):
    """Input model for protecting a branch in a GitLab repository.

    Attributes:
        project_path: The path of the project (e.g., 'namespace/project').
        branch_name: The name of the branch to protect.
        allowed_to_push: List of access levels allowed to push to the branch.
        allowed_to_merge: List of access levels allowed to merge to the branch.
        allow_force_push: Whether to allow force push to the branch.
        code_owner_approval_required: Whether code owner approval is required.
    """

    project_path: str
    branch_name: str
    allowed_to_push: list[AccessLevelModel]
    allowed_to_merge: list[AccessLevelModel]
    allow_force_push: bool = False
    code_owner_approval_required: bool = False


class UnprotectBranchInput(BaseModel):
    """Input model for unprotecting a branch in a GitLab repository.

    Attributes:
        project_path: The path of the project (e.g., 'namespace/project').
        branch_name: The name of the branch to unprotect.
    """

    project_path: str
    branch_name: str
