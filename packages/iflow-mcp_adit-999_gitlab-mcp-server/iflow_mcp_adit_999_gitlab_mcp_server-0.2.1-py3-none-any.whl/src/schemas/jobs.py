"""Schema definitions for GitLab CI/CD jobs."""

from pydantic import BaseModel


class JobLogsInput(BaseModel):
    """Input model for job logs.

    Attributes:
        project_path: The path to the project.
        job_id: The ID of the job.
    """

    project_path: str
    job_id: int


class JobLogsResponse(BaseModel):
    """Response model for GitLab job logs.

    Attributes:
        content: The content of the job logs.
    """

    content: str
