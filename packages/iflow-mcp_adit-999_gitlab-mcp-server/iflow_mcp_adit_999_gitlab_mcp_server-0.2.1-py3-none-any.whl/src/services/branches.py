"""Service functions for interacting with GitLab branches using the REST API."""

from typing import cast

from src.api.custom_exceptions import GitLabAPIError, GitLabErrorType
from src.api.rest_client import gitlab_rest_client
from src.schemas.branches import (
    CreateBranchInput,
    DeleteBranchInput,
    DeleteMergedBranchesInput,
    GetBranchInput,
    GetDefaultBranchRefInput,
    GitLabBranchList,
    GitLabReference,
    ListBranchesInput,
    ProtectBranchInput,
    UnprotectBranchInput,
)


async def create_branch(input_model: CreateBranchInput) -> GitLabReference:
    """Create a new branch in a GitLab repository using the REST API.

    Args:
        input_model: The input model containing project path, branch name, and ref.

    Returns:
        GitLabReference: The created branch details.

    Raises:
        GitLabAPIError: If the branch creation operation fails.
    """
    try:
        project_path = gitlab_rest_client._encode_path_parameter(
            input_model.project_path
        )
        endpoint = f"/projects/{project_path}/repository/branches"
        payload = {"branch": input_model.branch_name, "ref": input_model.ref}

        data = await gitlab_rest_client.post_async(endpoint, json_data=payload)

        return GitLabReference(
            name=data["name"],
            commit=data["commit"],
        )
    except GitLabAPIError as exc:
        if "already exists" in str(exc).lower():
            raise GitLabAPIError(
                GitLabErrorType.INVALID_REQUEST,
                {"message": f"Branch {input_model.branch_name} already exists"},
            ) from exc
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to create branch {input_model.branch_name}",
                "operation": "create_branch",
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": "Internal error during branch creation",
                "operation": "create_branch",
            },
        ) from exc


async def get_default_branch_ref(input_model: GetDefaultBranchRefInput) -> str:
    """Get the default branch reference for a GitLab repository.

    Args:
        input_model: The input model containing project path.

    Returns:
        str: The default branch reference.

    Raises:
        GitLabAPIError: If retrieving the default branch information fails.
    """
    try:
        project_path = gitlab_rest_client._encode_path_parameter(
            input_model.project_path
        )
        endpoint = f"/projects/{project_path}"

        data = await gitlab_rest_client.get_async(endpoint)
        return cast(str, data["default_branch"])
    except GitLabAPIError as exc:
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": "Failed to get default branch",
                "operation": "get_default_branch",
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": "Internal error getting default branch",
                "operation": "get_default_branch",
            },
        ) from exc


async def list_branches(input_model: ListBranchesInput) -> GitLabBranchList:
    """List branches in a GitLab repository.

    Args:
        input_model: The input model containing project path and optional search pattern.

    Returns:
        GitLabBranchList: List of branches in the repository.

    Raises:
        GitLabAPIError: If listing branches fails.
    """
    try:
        project_path = gitlab_rest_client._encode_path_parameter(
            input_model.project_path
        )
        endpoint = f"/projects/{project_path}/repository/branches"

        params = {}
        if input_model.search:
            params["search"] = input_model.search

        data = await gitlab_rest_client.get_async(endpoint, params=params)

        branches = [GitLabReference(**branch) for branch in data]
        return GitLabBranchList(items=branches)
    except GitLabAPIError as exc:
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {"message": "Failed to list branches", "operation": "list_branches"},
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": "Internal error listing branches",
                "operation": "list_branches",
            },
        ) from exc


async def get_branch(input_model: GetBranchInput) -> GitLabReference:
    """Get details for a specific branch in a GitLab repository.

    Args:
        input_model: The input model containing project path and branch name.

    Returns:
        GitLabReference: Details of the specified branch.

    Raises:
        GitLabAPIError: If retrieving branch details fails.
    """
    try:
        project_path = gitlab_rest_client._encode_path_parameter(
            input_model.project_path
        )
        branch_name = gitlab_rest_client._encode_path_parameter(input_model.branch_name)
        endpoint = f"/projects/{project_path}/repository/branches/{branch_name}"

        data = await gitlab_rest_client.get_async(endpoint)

        return GitLabReference(**data)
    except GitLabAPIError as exc:
        if "not found" in str(exc).lower():
            raise GitLabAPIError(
                GitLabErrorType.NOT_FOUND,
                {"message": f"Branch {input_model.branch_name} not found"},
            ) from exc
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to get branch {input_model.branch_name}",
                "operation": "get_branch",
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {"message": "Internal error getting branch", "operation": "get_branch"},
        ) from exc


async def delete_branch(input_model: DeleteBranchInput) -> bool:
    """Delete a branch from a GitLab repository.

    Args:
        input_model: The input model containing project path and branch name.

    Returns:
        bool: True if the branch was deleted, False if it was not found.

    Raises:
        GitLabAPIError: If deleting the branch fails unexpectedly.
    """
    try:
        project_path = gitlab_rest_client._encode_path_parameter(
            input_model.project_path
        )
        branch_name = gitlab_rest_client._encode_path_parameter(input_model.branch_name)
        endpoint = f"/projects/{project_path}/repository/branches/{branch_name}"
        await gitlab_rest_client.delete_async(endpoint)
        return True
    except GitLabAPIError as exc:
        if "not found" in str(exc).lower():
            return False
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to delete branch {input_model.branch_name}",
                "operation": "delete_branch",
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": "Internal error deleting branch",
                "operation": "delete_branch",
            },
        ) from exc


async def delete_merged_branches(input_model: DeleteMergedBranchesInput) -> bool:
    """Delete all merged branches from a GitLab repository.

    Args:
        input_model: The input model containing project path.

    Returns:
        bool: True if branches were deleted, False otherwise.

    Raises:
        GitLabAPIError: If deleting merged branches fails.
    """
    try:
        project_path = gitlab_rest_client._encode_path_parameter(
            input_model.project_path
        )
        endpoint = f"/projects/{project_path}/repository/merged_branches"

        await gitlab_rest_client.delete_async(endpoint)
        return True
    except GitLabAPIError as exc:
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": "Failed to delete merged branches",
                "operation": "delete_merged_branches",
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": "Internal error deleting merged branches",
                "operation": "delete_merged_branches",
            },
        ) from exc


async def protect_branch(input_model: ProtectBranchInput) -> bool:
    """Protect a branch in a GitLab repository.

    Args:
        input_model: The input model with protection settings.

    Returns:
        bool: True if the branch was protected successfully, False otherwise.

    Raises:
        GitLabAPIError: If protecting the branch fails unexpectedly.
    """
    try:
        project_path = gitlab_rest_client._encode_path_parameter(
            input_model.project_path
        )
        endpoint = f"/projects/{project_path}/protected_branches"

        allowed_to_push = [
            {"access_level": level.access_level}
            for level in input_model.allowed_to_push
        ]
        allowed_to_merge = [
            {"access_level": level.access_level}
            for level in input_model.allowed_to_merge
        ]
        payload = {
            "name": input_model.branch_name,
            "allowed_to_push": allowed_to_push,
            "allowed_to_merge": allowed_to_merge,
            "allow_force_push": input_model.allow_force_push,
            "code_owner_approval_required": input_model.code_owner_approval_required,
        }
        await gitlab_rest_client.post_async(endpoint, json_data=payload)
        return True
    except GitLabAPIError as exc:
        if "already protected" in str(exc).lower():
            return False
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to protect branch {input_model.branch_name}",
                "operation": "protect_branch",
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": "Internal error protecting branch",
                "operation": "protect_branch",
            },
        ) from exc


async def unprotect_branch(input_model: UnprotectBranchInput) -> bool:
    """Unprotect a branch in a GitLab repository.

    Args:
        input_model: The input model containing project path and branch name.

    Returns:
        bool: True if the branch was unprotected, False if it was not protected.

    Raises:
        GitLabAPIError: If unprotecting the branch fails unexpectedly.
    """
    try:
        project_path = gitlab_rest_client._encode_path_parameter(
            input_model.project_path
        )
        branch_name = gitlab_rest_client._encode_path_parameter(input_model.branch_name)
        endpoint = f"/projects/{project_path}/protected_branches/{branch_name}"
        await gitlab_rest_client.delete_async(endpoint)
        return True
    except GitLabAPIError as exc:
        if "not found" in str(exc).lower():
            return False
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to unprotect branch {input_model.branch_name}",
                "operation": "unprotect_branch",
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": "Internal error unprotecting branch",
                "operation": "unprotect_branch",
            },
        ) from exc
