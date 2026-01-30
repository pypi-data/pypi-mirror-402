from mcp.server.fastmcp import FastMCP

from src.services.branches import (
    create_branch,
    delete_branch,
    delete_merged_branches,
    get_branch,
    get_default_branch_ref,
    list_branches,
    protect_branch,
    unprotect_branch,
)
from src.services.files import (
    create_file,
    delete_file,
    get_file_contents,
    update_file,
)
from src.services.groups import (
    get_group,
    get_group_by_project_namespace,
    list_groups,
)
from src.services.issues import (
    close_issue,
    comment_on_issue,
    create_issue,
    delete_issue,
    get_issue,
    list_all_issues,
    list_issue_comments,
    move_issue,
)
from src.services.jobs import (
    get_job_logs,
)
from src.services.merge_requests import (
    create_merge_request,
    create_merge_request_comment,
    delete_merge_request,
    get_merge_request,
    list_merge_requests,
    merge_merge_request,
    merge_request_changes,
    update_merge_request,
)
from src.services.repositories import create_repository, list_repository_tree
from src.services.search import search_globally, search_group, search_project

# Create the MCP server
mcp = FastMCP("Gitlab", instructions="Use the tools to interact with GitLab.")

# Register repository tools

mcp.tool(name="create_repository", description="Create a new GitLab repository.")(
    create_repository
)
mcp.tool(
    name="list_repository_tree",
    description="List files and directories in a GitLab repository.",
)(list_repository_tree)


# Register branch tools
mcp.tool(
    name="create_branch", description="Create a new branch in a GitLab repository."
)(create_branch)
mcp.tool(
    name="get_default_branch_ref",
    description="Get the default branch reference for a GitLab repository.",
)(get_default_branch_ref)
mcp.tool(
    name="list_branches",
    description="List branches in a GitLab repository.",
)(list_branches)
mcp.tool(
    name="get_branch",
    description="Get details for a specific GitLab branch.",
)(get_branch)
mcp.tool(
    name="delete_branch",
    description="Delete a branch from a GitLab repository.",
)(delete_branch)
mcp.tool(
    name="delete_merged_branches",
    description="Delete all merged branches from a GitLab repository.",
)(delete_merged_branches)
mcp.tool(
    name="protect_branch",
    description="Protect a branch in a GitLab repository.",
)(protect_branch)
mcp.tool(
    name="unprotect_branch",
    description="Remove protection from a GitLab repository.",
)(unprotect_branch)

# Register file tools

mcp.tool(
    name="create_file",
    description="Create a new file in a GitLab repository.",
)(create_file)
mcp.tool(
    name="get_file_contents",
    description="Retrieve the contents of a file from a GitLab repository.",
)(get_file_contents)

mcp.tool(
    name="update_file",
    description="Update an existing file in a GitLab repository.",
)(update_file)
mcp.tool(
    name="delete_file",
    description="Delete a file from a GitLab repository.",
)(delete_file)

# Register issue tools
mcp.tool(name="create_issue", description="Create a new issue in a GitLab repository.")(
    create_issue
)

mcp.tool(
    name="list_all_issues",
    description="List all issues the authenticated user has access to.",
)(list_all_issues)

mcp.tool(name="get_issue", description="Get details for a specific GitLab issue.")(
    get_issue
)
mcp.tool(name="close_issue", description="Close a GitLab issue.")(close_issue)
mcp.tool(name="delete_issue", description="Delete an issue from a GitLab repository.")(
    delete_issue
)
mcp.tool(name="move_issue", description="Move an issue to a different project.")(
    move_issue
)
mcp.tool(name="comment_on_issue", description="Add a comment to a GitLab issue.")(
    comment_on_issue
)

mcp.tool(
    name="list_issue_comments",
    description="List comments on a specific GitLab issue.",
)(list_issue_comments)

# Register merge request tools
mcp.tool(
    name="create_merge_request",
    description="Create a new merge request in a GitLab repository.",
)(create_merge_request)
mcp.tool(
    name="list_merge_requests", description="List merge requests for a GitLab project."
)(list_merge_requests)
mcp.tool(
    name="get_merge_request",
    description="Get details for a specific GitLab merge request.",
)(get_merge_request)
mcp.tool(name="merge_merge_request", description="Merge a GitLab merge request.")(
    merge_merge_request
)
mcp.tool(
    name="update_merge_request",
    description="Update an existing merge request in GitLab.",
)(update_merge_request)
mcp.tool(
    name="delete_merge_request",
    description="Delete a merge request from a GitLab repository.",
)(delete_merge_request)
mcp.tool(
    name="merge_request_changes", description="Get the changes for a merge request."
)(merge_request_changes)
mcp.tool(
    name="create_merge_request_comment", description="Add a comment to a merge request."
)(create_merge_request_comment)

# Register job tools

mcp.tool(
    name="get_job_logs",
    description="Get logs from a GitLab job.",
)(get_job_logs)


# Register group tools
mcp.tool(name="list_groups", description="List GitLab groups.")(list_groups)
mcp.tool(name="get_group", description="Get a specific GitLab group.")(get_group)
mcp.tool(
    name="get_group_by_project_namespace",
    description="Get a GitLab group based on a project namespace.",
)(get_group_by_project_namespace)


# Register search tools
mcp.tool(
    name="search_project",
    description="Search within a specific project. Supports searching for projects, blobs, and wiki blobs.",
)(search_project)
mcp.tool(
    name="search_globally",
    description="Search across all GitLab resources (projects, blobs, and wiki blobs).",
)(search_globally)
mcp.tool(
    name="search_group",
    description="Search within a specific group. Supports searching for projects, blobs, and wiki blobs.",
)(search_group)

# Run the server
if __name__ == "__main__":
    mcp.run(transport="stdio")

def main():
    mcp.run(transport="stdio")