"""Search service for GitLab API.

This module provides functions for searching across GitLab resources.
"""

from typing import Any

from src.api.custom_exceptions import GitLabAPIError, GitLabErrorType
from src.api.rest_client import gitlab_rest_client
from src.schemas.search import (
    BlobSearchResult,
    GlobalSearchRequest,
    GroupSearchRequest,
    ProjectSearchRequest,
    ProjectSearchResult,
    SearchScope,
)


def _parse_search_results(
    response: list[dict[str, Any]], scope: SearchScope
) -> list[Any]:
    """Parse search results for projects/blobs only, returning only minimal fields."""
    result_map = {
        SearchScope.PROJECTS: ProjectSearchResult,
        SearchScope.BLOBS: BlobSearchResult,
        SearchScope.WIKI_BLOBS: BlobSearchResult,
    }
    model_class = result_map.get(scope)
    if model_class is None:
        raise UnsupportedSearchScopeError(scope)
    minimal_keys = set(model_class.model_fields.keys())
    return [
        model_class.model_validate({k: v for k, v in item.items() if k in minimal_keys})
        for item in response
    ]


async def search_globally(search_term: str, scope: SearchScope) -> list[Any]:
    """Search across all resources in the GitLab instance (projects/blobs only)."""
    try:
        search_request = GlobalSearchRequest(scope=scope, search=search_term)
        response = await gitlab_rest_client.get_async(
            "/search",
            params={
                "scope": search_request.scope.value,
                "search": search_request.search,
            },
        )
        return _parse_search_results(response, scope)
    except GitLabAPIError as exc:
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to perform global search for term '{search_term}'",
                "operation": "search_globally",
                "scope": scope.value,
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": "Internal error performing global search",
                "operation": "search_globally",
                "scope": scope.value,
            },
        ) from exc


async def search_group(
    group_id: str, search_term: str, scope: SearchScope
) -> list[Any]:
    """Search within a specific group (projects/blobs only)."""
    try:
        search_request = GroupSearchRequest(
            group_id=group_id, scope=scope, search=search_term
        )
        response = await gitlab_rest_client.get_async(
            f"/groups/{search_request.group_id}/search",
            params={
                "scope": search_request.scope.value,
                "search": search_request.search,
            },
        )
        return _parse_search_results(response, scope)
    except GitLabAPIError as exc:
        if "not found" in str(exc).lower():
            raise GitLabAPIError(
                GitLabErrorType.NOT_FOUND,
                {"message": f"Group {group_id} not found"},
            ) from exc
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to search group {group_id} for term '{search_term}'",
                "operation": "search_group",
                "scope": scope.value,
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": "Internal error performing group search",
                "operation": "search_group",
                "scope": scope.value,
            },
        ) from exc


async def search_project(input_model: ProjectSearchRequest) -> list[Any]:
    """Search within a specific project using a validated input model (projects/blobs only)."""

    try:
        params = {
            "scope": input_model.scope.value,
            "search": input_model.search,
        }
        if input_model.ref:
            params["ref"] = input_model.ref
        response = await gitlab_rest_client.get_async(
            f"/projects/{input_model.project_id}/search",
            params=params,
        )
        return _parse_search_results(response, input_model.scope)
    except GitLabAPIError as exc:
        if "not found" in str(exc).lower():
            raise GitLabAPIError(
                GitLabErrorType.NOT_FOUND,
                {"message": f"Project {input_model.project_id} not found"},
            ) from exc
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to search project {input_model.project_id} for term '{input_model.search}'",
                "operation": "search_project",
                "scope": input_model.scope.value,
            },
        ) from exc
    except Exception as exc:
        raise GitLabAPIError(
            GitLabErrorType.SERVER_ERROR,
            {
                "message": "Internal error performing project search",
                "operation": "search_project",
                "scope": input_model.scope.value,
            },
        ) from exc


class UnsupportedSearchScopeError(Exception):
    def __init__(self, scope: Any) -> None:
        super().__init__(f"Unsupported search scope: {scope}")
