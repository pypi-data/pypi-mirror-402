"""Service functions for interacting with GitLab repositories using the REST API."""

from typing import Any

from src.api.custom_exceptions import GitLabAPIError, GitLabErrorType
from src.api.rest_client import gitlab_rest_client
from src.schemas.repositories import (
    CreateRepositoryInput,
    GitLabRepository,
    ListRepositoryTreeInput,
    RepositoryTreeResponse,
)


async def create_repository(input_model: CreateRepositoryInput) -> GitLabRepository:
    """Create a new GitLab repository using the REST API.

    Args:
        input_model: The input model containing repository details.

    Returns:
        GitLabRepository: The created repository details.

    Raises:
        GitLabAPIError: If the GitLab API returns an error.
    """
    try:
        payload = {
            "name": input_model.name,
            "description": input_model.description,
            "visibility": input_model.visibility.value,
            "initialize_with_readme": input_model.initialize_with_readme,
        }
        response = await gitlab_rest_client.post_async("/projects", json_data=payload)
        return GitLabRepository(
            id=response["id"],
            name=response["name"],
            path=response["path"],
            description=response.get("description"),
            web_url=response["web_url"],
            default_branch=response.get("default_branch"),
        )
    except GitLabAPIError:
        raise
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": f"Internal error creating repository: {exc!s}",
                "operation": "create_repository",
            },
        ) from exc


async def list_repository_tree(
    input_model: ListRepositoryTreeInput,
) -> RepositoryTreeResponse:
    """List files and directories in a repository.

    Args:
        input_model: Input parameters containing project path and optional filters.

    Returns:
        RepositoryTreeResponse: A response containing the list of files and directories.

    Raises:
        GitLabAPIError: If the GitLab API returns an error.
    """
    try:
        encoded_path = gitlab_rest_client._encode_path_parameter(
            input_model.project_path
        )

        params: dict[str, Any] = {"per_page": input_model.per_page}
        if input_model.ref:
            params["ref"] = input_model.ref
        if input_model.recursive:
            params["recursive"] = str(input_model.recursive).lower()

        response = await gitlab_rest_client.get_async(
            f"/projects/{encoded_path}/repository/tree", params=params
        )

        return response
    except GitLabAPIError as exc:
        if "not found" in str(exc).lower():
            raise GitLabAPIError(
                GitLabErrorType.NOT_FOUND,
                {"message": f"Project {input_model.project_path} not found"},
            ) from exc
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to list repository contents for {input_model.project_path}",
                "operation": "list_repository_contents",
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": "Internal error listing repository contents",
                "operation": "list_repository_contents",
            },
        ) from exc
