"""Service functions for interacting with GitLab groups using the REST API."""

from src.api.custom_exceptions import GitLabAPIError, GitLabErrorType
from src.api.rest_client import gitlab_rest_client
from src.schemas.groups import (
    GetGroupByProjectNamespaceInput,
    GetGroupInput,
    GitLabGroup,
    GitLabGroupListResponse,
    ListGroupsInput,
)


async def list_groups(input_model: ListGroupsInput) -> GitLabGroupListResponse:
    """List GitLab groups using the REST API.

    Args:
        input_model: The input model containing filter parameters.

    Returns:
        GitLabGroupListResponse: The paginated list of groups.

    Raises:
        GitLabAPIError: If retrieving the groups fails.
    """
    # Prepare query parameters
    params = {}

    # Add pagination parameters
    params["page"] = input_model.page
    params["per_page"] = input_model.per_page

    # Add filtering parameters
    if input_model.search:
        params["search"] = input_model.search
    if input_model.owned:
        params["owned"] = "true"
    if input_model.min_access_level:
        params["min_access_level"] = str(input_model.min_access_level.value)
    if input_model.top_level_only:
        params["top_level_only"] = "true"

    try:
        # Make the API call
        response_data = await gitlab_rest_client.get_async("/groups", params=params)

        # Get total count - in a real implementation we would use the headers
        # For now, just use the length of the response
        total_count = len(response_data)

        # Parse the response into our schema
        items = [GitLabGroup.model_validate(group) for group in response_data]

        return GitLabGroupListResponse(
            items=items,
            count=total_count,
        )
    except GitLabAPIError:
        raise  # Re-raise GitLabAPIError as is
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR, {"operation": "list_groups"}, code=500
        ) from exc


async def get_group(input_model: GetGroupInput) -> GitLabGroup:
    """Get a specific GitLab group using the REST API.

    Args:
        input_model: The input model containing the group ID or path.

    Returns:
        GitLabGroup: The requested group.

    Raises:
        GitLabAPIError: If the group does not exist or if retrieving the group fails.
    """
    # Encode the group ID/path
    group_id = gitlab_rest_client._encode_path_parameter(input_model.group_id)

    try:
        # Make the API call
        response = await gitlab_rest_client.get_async(f"/groups/{group_id}")

        # Parse the response into our schema
        return GitLabGroup.model_validate(response)
    except GitLabAPIError as exc:
        if "not found" in str(exc).lower():
            raise GitLabAPIError(
                GitLabErrorType.NOT_FOUND, {"group_id": input_model.group_id}, code=404
            ) from exc
        raise  # Re-raise original GitLabAPIError for other API errors
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {"operation": "get_group", "group_id": input_model.group_id},
            code=500,
        ) from exc


async def get_group_by_project_namespace(
    input_model: GetGroupByProjectNamespaceInput,
) -> GitLabGroup:
    """Get a GitLab group based on a project namespace using the REST API.

    Args:
        input_model: The input model containing the project namespace.

    Returns:
        GitLabGroup: The requested group.

    Raises:
        GroupNamespaceError: If retrieving the group for the namespace fails.
        GitLabAPIError: If retrieving the group fails for other reasons.
    """
    # In GitLab, the project namespace is the group path or subgroup path
    # We'll encode it as a path parameter
    namespace = gitlab_rest_client._encode_path_parameter(input_model.project_namespace)

    try:
        # Make the API call
        response = await gitlab_rest_client.get_async(f"/groups/{namespace}")

        # Parse the response into our schema
        return GitLabGroup.model_validate(response)
    except GitLabAPIError as exc:
        if "not found" in str(exc).lower():
            raise GitLabAPIError(
                GitLabErrorType.NOT_FOUND,
                {"namespace": input_model.project_namespace},
                code=404,
            ) from exc
        raise  # Re-raise original GitLabAPIError for other API errors
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "operation": "get_group_by_namespace",
                "namespace": input_model.project_namespace,
            },
            code=500,
        ) from exc
