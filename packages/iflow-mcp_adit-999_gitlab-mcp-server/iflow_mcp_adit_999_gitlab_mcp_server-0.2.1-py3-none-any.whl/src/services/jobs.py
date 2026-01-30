"""Services for interacting with GitLab CI/CD jobs."""

from src.api.custom_exceptions import GitLabAPIError, GitLabErrorType
from src.api.rest_client import gitlab_rest_client
from src.schemas.jobs import JobLogsInput, JobLogsResponse


async def get_job_logs(input_model: JobLogsInput) -> JobLogsResponse:
    """Get logs for a job.

    Args:
         input_model: The input parameters containing project_path and job_id.
    Returns:
        The job logs.
    """
    try:
        project_path = gitlab_rest_client._encode_path_parameter(
            input_model.project_path
        )
        job_id = input_model.job_id
        response = await gitlab_rest_client.get_async(
            f"/projects/{project_path}/jobs/{job_id}/trace"
        )

        return JobLogsResponse(content=response)
    except GitLabAPIError as exc:
        raise GitLabAPIError(
            GitLabErrorType.REQUEST_FAILED,
            {
                "message": f"Failed to get job logs for job {input_model.job_id}",
                "operation": "get_job_logs",
            },
        ) from exc
