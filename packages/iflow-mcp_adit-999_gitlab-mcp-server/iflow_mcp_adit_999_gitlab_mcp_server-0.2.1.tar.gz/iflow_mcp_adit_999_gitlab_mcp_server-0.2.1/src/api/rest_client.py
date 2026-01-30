"""REST client for making HTTP requests to the GitLab API."""

import os
from collections.abc import AsyncIterator
from typing import Any

import httpx

from src.api.custom_exceptions import GitLabAPIError, GitLabAuthError, GitLabErrorType


class GitLabRestClient:
    """GitLab REST API client using httpx."""

    def __init__(self) -> None:
        """Initialize the GitLab REST client."""
        self._base_url = os.getenv("GITLAB_API_URL", "https://gitlab.com")
        self._token = os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN")
        self._httpx_client: httpx.AsyncClient | None = None

    def _get_headers(self) -> dict[str, str]:
        """Get headers for authenticating with the GitLab API.

        Returns:
            The headers including authentication token.

        Raises:
            GitLabAuthError: If the authentication token is not set.
        """
        if not self._token:
            raise GitLabAuthError()
        return {"PRIVATE-TOKEN": self._token}

    def get_api_url(self) -> str:
        """Get the base URL for the GitLab API.

        Returns:
            The GitLab API base URL.
        """
        return self._base_url

    def get_httpx_client(self) -> httpx.AsyncClient:
        """Get or create an async HTTP client.

        Returns:
            The async HTTP client.
        """
        if self._httpx_client is None:
            self._httpx_client = httpx.AsyncClient(base_url=f"{self._base_url}/api/v4")
        return self._httpx_client

    async def aclose(self) -> None:
        """Close the async HTTP client."""
        if self._httpx_client is not None:
            await self._httpx_client.aclose()
            self._httpx_client = None

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from the GitLab API.

        Args:
            response: The HTTP response.

        Raises:
            GitLabAPIError: If the response indicates an error.
        """
        raise GitLabAPIError.from_response(response)

    def _encode_path_parameter(self, param: str) -> str:
        """URL encode a path parameter for use in GitLab API URLs.

        Args:
            param: The parameter to encode.

        Returns:
            The encoded parameter.
        """
        return param.replace("/", "%2F")

    async def get_async(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Make an async GET request to the GitLab API.

        Args:
            path: The API endpoint path.
            params: Optional query parameters.

        Returns:
            The JSON response.

        Raises:
            GitLabAPIError: If the request fails.
        """
        client = self.get_httpx_client()
        headers = self._get_headers()

        try:
            response = await client.get(path, headers=headers, params=params)
            if response.is_success:
                return response.json()
            self._handle_error_response(response)
        except httpx.HTTPError as exc:
            raise GitLabAPIError(
                GitLabErrorType.REQUEST_FAILED,
                {"message": str(exc), "action": "get"},
            ) from exc

    async def post_async(
        self, path: str, json_data: dict[str, Any], params: dict[str, Any] | None = None
    ) -> Any:
        """Make an async POST request to the GitLab API.

        Args:
            path: The API endpoint path.
            json_data: The JSON data to send.
            params: Optional query parameters.

        Returns:
            The JSON response.

        Raises:
            GitLabAPIError: If the request fails.
        """
        client = self.get_httpx_client()
        headers = self._get_headers()

        try:
            response = await client.post(
                path, headers=headers, json=json_data, params=params
            )
            if response.is_success:
                return response.json()
            self._handle_error_response(response)
        except httpx.HTTPError as exc:
            raise GitLabAPIError(
                GitLabErrorType.REQUEST_FAILED,
                {"message": str(exc), "action": "post"},
            ) from exc

    async def put_async(
        self, path: str, json_data: dict[str, Any], params: dict[str, Any] | None = None
    ) -> Any:
        """Make an async PUT request to the GitLab API.

        Args:
            path: The API endpoint path.
            json_data: The JSON data to send.
            params: Optional query parameters.

        Returns:
            The JSON response.

        Raises:
            GitLabAPIError: If the request fails.
        """
        client = self.get_httpx_client()
        headers = self._get_headers()

        try:
            response = await client.put(
                path, headers=headers, json=json_data, params=params
            )
            if response.is_success:
                return response.json()
            self._handle_error_response(response)
        except httpx.HTTPError as exc:
            raise GitLabAPIError(
                GitLabErrorType.REQUEST_FAILED,
                {"message": str(exc), "action": "put"},
            ) from exc

    async def delete_async(
        self, path: str, params: dict[str, Any] | None = None
    ) -> Any:
        """Make an async DELETE request to the GitLab API.

        Args:
            path: The API endpoint path.
            params: Optional query parameters.

        Returns:
            The JSON response or None if no content.

        Raises:
            GitLabAPIError: If the request fails.
        """
        client = self.get_httpx_client()
        headers = self._get_headers()

        try:
            response = await client.delete(path, headers=headers, params=params)
            if response.is_success:
                if response.text:
                    return response.json()
                return None
            self._handle_error_response(response)
        except httpx.HTTPError as exc:
            raise GitLabAPIError(
                GitLabErrorType.REQUEST_FAILED,
                {"message": str(exc), "action": "delete"},
            ) from exc

    async def paginate_async(
        self, path: str, params: dict[str, Any] | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        """Paginate through a GitLab API endpoint.

        Args:
            path: The API endpoint path.
            params: Optional query parameters.

        Yields:
            Each item in the paginated response.

        Raises:
            GitLabAPIError: If the request fails.
        """
        if params is None:
            params = {}

        params = params.copy()
        page = params.pop("page", 1)
        per_page = params.pop("per_page", 20)

        while True:
            page_params = {"page": page, "per_page": per_page, **params}
            client = self.get_httpx_client()
            headers = self._get_headers()

            try:
                response = await client.get(path, headers=headers, params=page_params)
                if not response.is_success:
                    self._handle_error_response(response)

                data = response.json()
                if not data or not isinstance(data, list):
                    break

                for item in data:
                    yield item

                if len(data) < per_page:
                    break

                page += 1
            except httpx.HTTPError as exc:
                raise GitLabAPIError(
                    GitLabErrorType.REQUEST_FAILED,
                    {"message": str(exc), "action": "paginate"},
                ) from exc


# Singleton instance for global use
gitlab_rest_client = GitLabRestClient()
