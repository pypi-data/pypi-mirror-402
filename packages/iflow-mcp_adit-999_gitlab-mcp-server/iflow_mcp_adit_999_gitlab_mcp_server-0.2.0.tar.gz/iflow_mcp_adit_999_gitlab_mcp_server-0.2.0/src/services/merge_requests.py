"""Services for interacting with GitLab merge requests."""

from dataclasses import dataclass

from src.api.custom_exceptions import GitLabAPIError, GitLabErrorType
from src.api.rest_client import gitlab_rest_client
from src.schemas.base import PaginatedResponse
from src.schemas.merge_requests import (
    AcceptedMergeRequest,
    CreateMergeRequestInput,
    GitLabComment,
    GitLabMergeRequest,
    ListMergeRequestsInput,
    MergeRequestChanges,
    UpdateMergeRequestInput,
)


@dataclass
class MergeOptions:
    """Options for merging a merge request."""

    merge_commit_message: str | None = None
    squash_commit_message: str | None = None
    auto_merge: bool | None = None
    should_remove_source_branch: bool | None = None
    sha: str | None = None
    squash: bool | None = None


async def create_merge_request(
    input_model: CreateMergeRequestInput,
) -> GitLabMergeRequest:
    """Create a new merge request.

    Args:
        input_model: The input model containing merge request details.

    Returns:
        GitLabMergeRequest: The created merge request details.

    Raises:
        GitLabAPIError: If creating the merge request fails.
    """
    try:
        project_path = gitlab_rest_client._encode_path_parameter(
            input_model.project_path
        )

        payload = input_model.model_dump(exclude={"project_path"}, exclude_none=True)

        response = await gitlab_rest_client.post_async(
            f"/projects/{project_path}/merge_requests", json_data=payload
        )

        return GitLabMergeRequest.model_validate(response)
    except GitLabAPIError as exc:
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": "Failed to create merge request",
                "details": str(exc),
                "operation": "create_merge_request",
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": "Internal error creating merge request",
                "operation": "create_merge_request",
            },
        ) from exc


async def list_merge_requests(
    input_model: ListMergeRequestsInput,
) -> PaginatedResponse[GitLabMergeRequest]:
    """List merge requests for a project.

    Args:
        input_model: The input model containing query parameters.

    Returns:
        PaginatedResponse[GitLabMergeRequest]: A paginated response of merge requests.

    Raises:
        GitLabAPIError: If retrieving the merge requests fails.
    """
    try:
        project_path = gitlab_rest_client._encode_path_parameter(
            input_model.project_path
        )

        params = input_model.model_dump(
            exclude={"project_path"},
            exclude_none=True,
        )

        # Convert state enum to string if present
        if "state" in params and params["state"] is not None:
            params["state"] = params["state"].value

        # Convert labels list to comma-separated string if present
        if "labels" in params and params["labels"] is not None:
            params["labels"] = ",".join(params["labels"])

        response = await gitlab_rest_client.get_async(
            f"/projects/{project_path}/merge_requests",
            params=params,
        )

        # Try to get pagination count from headers if available (simulate for now)
        # In a real implementation, headers would be available from the HTTP client
        count = len(response)
        items = [GitLabMergeRequest.model_validate(mr) for mr in response]

        return PaginatedResponse[GitLabMergeRequest](count=count, items=items)
    except GitLabAPIError as exc:
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to list merge requests for project {input_model.project_path}",
                "operation": "list_merge_requests",
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": "Internal error listing merge requests",
                "operation": "list_merge_requests",
            },
        ) from exc


async def get_merge_request(
    project_path: str,
    mr_iid: int,
    include_diverged_commits_count: bool = False,
    include_rebase_in_progress: bool = False,
    render_html: bool = False,
) -> GitLabMergeRequest:
    """Get a specific merge request.

    Args:
        project_path: The path of the project.
        mr_iid: The internal ID of the merge request.
        include_diverged_commits_count: Whether to include the count of diverged commits.
        include_rebase_in_progress: Whether to include rebase in progress status.
        render_html: Whether to render HTML for title and description.

    Returns:
        GitLabMergeRequest: The merge request details.

    Raises:
        GitLabAPIError: If retrieving the merge request fails.
    """
    try:
        project_path_encoded = gitlab_rest_client._encode_path_parameter(project_path)

        params = {
            "include_diverged_commits_count": include_diverged_commits_count,
            "include_rebase_in_progress": include_rebase_in_progress,
            "render_html": render_html,
        }

        response = await gitlab_rest_client.get_async(
            f"/projects/{project_path_encoded}/merge_requests/{mr_iid}",
            params=params,
        )

        return GitLabMergeRequest.model_validate(response)
    except GitLabAPIError as exc:
        if "not found" in str(exc).lower():
            raise GitLabAPIError(
                GitLabErrorType.NOT_FOUND,
                {"message": f"Merge request {mr_iid} not found"},
            ) from exc
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to get merge request {mr_iid}",
                "operation": "get_merge_request",
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": "Internal error getting merge request",
                "operation": "get_merge_request",
            },
        ) from exc


async def update_merge_request(
    input_model: UpdateMergeRequestInput,
) -> GitLabMergeRequest:
    """Update a merge request.

    Args:
        input_model: The input model containing update fields.

    Returns:
        GitLabMergeRequest: The updated merge request details.

    Raises:
        GitLabAPIError: If updating the merge request fails.
    """
    try:
        project_path_encoded = gitlab_rest_client._encode_path_parameter(
            input_model.project_path
        )
        mr_iid = input_model.mr_iid

        payload = input_model.model_dump(
            exclude={"project_path", "mr_iid"},
            exclude_none=True,
        )
        for key in ("labels", "add_labels", "remove_labels"):
            if key in payload and payload[key] is not None:
                payload[key] = ",".join(payload[key])

        response = await gitlab_rest_client.put_async(
            f"/projects/{project_path_encoded}/merge_requests/{mr_iid}",
            json_data=payload,
        )
        return GitLabMergeRequest.model_validate(response)
    except GitLabAPIError as exc:
        if "not found" in str(exc).lower():
            raise GitLabAPIError(
                GitLabErrorType.NOT_FOUND,
                {"message": f"Merge request {input_model.mr_iid} not found"},
            ) from exc
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to update merge request {input_model.mr_iid}",
                "details": str(exc),
                "operation": "update_merge_request",
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": "Internal error updating merge request",
                "operation": "update_merge_request",
            },
        ) from exc


async def delete_merge_request(project_path: str, mr_iid: int) -> None:
    """Delete a merge request.

    Args:
        project_path: The path of the project.
        mr_iid: The internal ID of the merge request.

    Raises:
        GitLabAPIError: If deleting the merge request fails.
    """
    try:
        project_path_encoded = gitlab_rest_client._encode_path_parameter(project_path)

        await gitlab_rest_client.delete_async(
            f"/projects/{project_path_encoded}/merge_requests/{mr_iid}"
        )
    except GitLabAPIError as exc:
        if "not found" in str(exc).lower():
            raise GitLabAPIError(
                GitLabErrorType.NOT_FOUND,
                {"message": f"Merge request {mr_iid} not found"},
            ) from exc
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to delete merge request {mr_iid}",
                "operation": "delete_merge_request",
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": "Internal error deleting merge request",
                "operation": "delete_merge_request",
            },
        ) from exc


async def merge_request_changes(project_path: str, mr_iid: int) -> MergeRequestChanges:
    """Get the changes of a merge request.

    Args:
        project_path: The path of the project.
        mr_iid: The internal ID of the merge request.

    Returns:
        MergeRequestChanges: The changes in the merge request.

    Raises:
        GitLabAPIError: If retrieving the changes fails.
    """
    try:
        project_path_encoded = gitlab_rest_client._encode_path_parameter(project_path)

        response = await gitlab_rest_client.get_async(
            f"/projects/{project_path_encoded}/merge_requests/{mr_iid}/changes"
        )

        return MergeRequestChanges.model_validate(response)
    except GitLabAPIError as exc:
        if "not found" in str(exc).lower():
            raise GitLabAPIError(
                GitLabErrorType.NOT_FOUND,
                {"message": f"Merge request {mr_iid} not found"},
            ) from exc
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to get changes for merge request {mr_iid}",
                "operation": "merge_request_changes",
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": "Internal error getting merge request changes",
                "operation": "merge_request_changes",
            },
        ) from exc


async def merge_merge_request(
    project_path: str, mr_iid: int, options: MergeOptions | None = None
) -> AcceptedMergeRequest:
    """Merge a merge request.

    Args:
        project_path: The path of the project.
        mr_iid: The internal ID of the merge request.
        options: Options for merging the merge request.

    Returns:
        AcceptedMergeRequest: The merged merge request details.

    Raises:
        GitLabAPIError: If merging the merge request fails.
    """
    try:
        project_path_encoded = gitlab_rest_client._encode_path_parameter(project_path)

        if options is None:
            options = MergeOptions()

        payload = {
            "merge_commit_message": options.merge_commit_message,
            "squash_commit_message": options.squash_commit_message,
            "auto_merge": options.auto_merge,
            "should_remove_source_branch": options.should_remove_source_branch,
            "sha": options.sha,
            "squash": options.squash,
        }

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        response = await gitlab_rest_client.put_async(
            f"/projects/{project_path_encoded}/merge_requests/{mr_iid}/merge",
            json_data=payload,
        )

        return AcceptedMergeRequest.model_validate(response)
    except GitLabAPIError as exc:
        if "not found" in str(exc).lower():
            raise GitLabAPIError(
                GitLabErrorType.NOT_FOUND,
                {"message": f"Merge request {mr_iid} not found"},
            ) from exc
        if (
            "cannot be merged" in str(exc).lower()
            or "is not mergeable" in str(exc).lower()
        ):
            raise GitLabAPIError(
                GitLabErrorType.INVALID_REQUEST,
                {
                    "message": f"Merge request {mr_iid} cannot be merged",
                    "details": str(exc),
                },
            ) from exc
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to merge merge request {mr_iid}",
                "operation": "merge_merge_request",
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": "Internal error merging merge request",
                "operation": "merge_merge_request",
            },
        ) from exc


async def create_merge_request_comment(
    project_path: str, mr_iid: int, body: str
) -> GitLabComment:
    """Create a comment on a merge request.

    Args:
        project_path: The path of the project.
        mr_iid: The internal ID of the merge request.
        body: The content of the comment.

    Returns:
        GitLabComment: The created comment.

    Raises:
        GitLabAPIError: If creating the comment fails.
    """
    try:
        project_path_encoded = gitlab_rest_client._encode_path_parameter(project_path)

        response = await gitlab_rest_client.post_async(
            f"/projects/{project_path_encoded}/merge_requests/{mr_iid}/notes",
            json_data={"body": body},
        )

        return GitLabComment.model_validate(response)
    except GitLabAPIError as exc:
        if "not found" in str(exc).lower():
            raise GitLabAPIError(
                GitLabErrorType.NOT_FOUND,
                {"message": f"Merge request {mr_iid} not found"},
            ) from exc
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to comment on merge request {mr_iid}",
                "operation": "create_merge_request_comment",
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": "Internal error creating merge request comment",
                "operation": "create_merge_request_comment",
            },
        ) from exc
