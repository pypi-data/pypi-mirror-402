"""Service functions for interacting with GitLab repository files using the REST API."""

import base64

from src.api.custom_exceptions import GitLabAPIError, GitLabErrorType
from src.api.rest_client import gitlab_rest_client
from src.schemas.files import (
    CreateFileInput,
    DeleteFileInput,
    FileOperationResponse,
    GetFileContentsInput,
    GitLabContent,
    UpdateFileInput,
)


async def get_file_contents(input_model: GetFileContentsInput) -> GitLabContent:
    """Retrieve the contents of a file from a GitLab repository using the REST API.

    Args:
        input_model: The input model containing project path, file path, and ref.

    Returns:
        GitLabContent: The file contents.

    Raises:
        GitLabAPIError: If retrieving the file content fails.
    """
    try:
        project_path = gitlab_rest_client._encode_path_parameter(
            input_model.project_path
        )
        ref = input_model.ref or "main"
        file_path = gitlab_rest_client._encode_path_parameter(input_model.file_path)

        endpoint = f"/projects/{project_path}/repository/files/{file_path}"
        params = {"ref": ref}

        data = await gitlab_rest_client.get_async(endpoint, params=params)

        # GitLab API returns base64 encoded content
        content = base64.b64decode(data["content"]).decode("utf-8")

        return GitLabContent(
            file_path=data["file_path"],
            content=content,
            encoding=data.get("encoding", "base64"),
            ref=ref,
            blob_id=data.get("blob_id"),
            commit_id=data.get("commit_id"),
            last_commit_id=data.get("last_commit_id"),
            content_sha256=data.get("content_sha256"),
            size=data.get("size"),
            execute_filemode=data.get("execute_filemode", False),
        )
    except GitLabAPIError as exc:
        if "not found" in str(exc).lower():
            raise GitLabAPIError(
                GitLabErrorType.NOT_FOUND,
                {"message": f"File {input_model.file_path} not found"},
            ) from exc
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to get file content for {input_model.file_path}",
                "operation": "get_file_contents",
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": "Internal error retrieving file content",
                "operation": "get_file_contents",
            },
        ) from exc


async def create_file(input_model: CreateFileInput) -> FileOperationResponse:
    """Create a new file in a GitLab repository using the REST API.

    Args:
        input_model: The input model containing file details and commit information.

    Returns:
        FileOperationResponse: Details of the created file.

    Raises:
        GitLabAPIError: If the file creation fails or the file already exists.
    """
    # Explicit input validation for required fields
    missing_fields = []
    for field in ("project_path", "file_path", "branch", "content", "commit_message"):
        if getattr(input_model, field, None) in (None, ""):
            missing_fields.append(field)
    if missing_fields:
        raise GitLabAPIError(
            GitLabErrorType.INVALID_REQUEST,
            {"message": f"Missing required fields: {', '.join(missing_fields)}"},
        )
    try:
        project_path = gitlab_rest_client._encode_path_parameter(
            input_model.project_path
        )
        file_path = gitlab_rest_client._encode_path_parameter(input_model.file_path)
        endpoint = f"/projects/{project_path}/repository/files/{file_path}"
        payload = {
            "branch": input_model.branch,
            "content": input_model.content,
            "commit_message": input_model.commit_message,
            "encoding": input_model.encoding,
        }
        await gitlab_rest_client.post_async(endpoint, json_data=payload)
        return FileOperationResponse(
            file_path=input_model.file_path,
            branch=input_model.branch,
        )
    except GitLabAPIError as exc:
        if "already exists" in str(exc).lower():
            raise GitLabAPIError(
                GitLabErrorType.INVALID_REQUEST,
                {"message": f"File {input_model.file_path} already exists"},
            ) from exc
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to create file {input_model.file_path}",
                "operation": "create_file",
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {"message": "Internal error creating file", "operation": "create_file"},
        ) from exc


async def update_file(input_model: UpdateFileInput) -> FileOperationResponse:
    """Update an existing file in a GitLab repository using the REST API.

    Args:
        input_model: The input model containing file details and commit information.

    Returns:
        FileOperationResponse: Details of the updated file.

    Raises:
        GitLabAPIError: If the file update fails or the file doesn't exist.
    """
    try:
        project_path = gitlab_rest_client._encode_path_parameter(
            input_model.project_path
        )
        file_path = gitlab_rest_client._encode_path_parameter(input_model.file_path)

        endpoint = f"/projects/{project_path}/repository/files/{file_path}"

        # Prepare payload
        payload = {
            "branch": input_model.branch,
            "content": input_model.content,
            "commit_message": input_model.commit_message,
            "encoding": input_model.encoding,
        }

        if input_model.last_commit_id:
            payload["last_commit_id"] = input_model.last_commit_id

        await gitlab_rest_client.put_async(endpoint, json_data=payload)

        return FileOperationResponse(
            file_path=input_model.file_path,
            branch=input_model.branch,
        )
    except GitLabAPIError as exc:
        if "not exist" in str(exc).lower():
            raise GitLabAPIError(
                GitLabErrorType.NOT_FOUND,
                {"message": f"File {input_model.file_path} not found"},
            ) from exc
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to update file {input_model.file_path}",
                "operation": "update_file",
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {"message": "Internal error updating file", "operation": "update_file"},
        ) from exc


async def delete_file(input_model: DeleteFileInput) -> bool:
    """Delete a file from a GitLab repository using the REST API.

    Args:
        input_model: The input model containing file path, branch, and commit information.

    Returns:
        bool: True if the file was deleted, False if it was not found.

    Raises:
        GitLabAPIError: If the file deletion fails unexpectedly.
    """
    try:
        project_path = gitlab_rest_client._encode_path_parameter(
            input_model.project_path
        )
        file_path = gitlab_rest_client._encode_path_parameter(input_model.file_path)
        endpoint = f"/projects/{project_path}/repository/files/{file_path}"
        params = {
            "branch": input_model.branch,
            "commit_message": input_model.commit_message,
        }
        await gitlab_rest_client.delete_async(endpoint, params=params)
        return True
    except GitLabAPIError as exc:
        if "not exist" in str(exc).lower() or "not found" in str(exc).lower():
            return False
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to delete file {input_model.file_path}",
                "operation": "delete_file",
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {"message": "Internal error deleting file", "operation": "delete_file"},
        ) from exc
