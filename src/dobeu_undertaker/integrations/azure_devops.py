"""
Azure DevOps integration for Dobeu Undertaker.

Provides functionality to:
- Update pipeline status
- Create pull request comments
- Manage build artifacts
- Report compliance status to Azure Boards
"""

import os
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from dobeu_undertaker.config.schema import AzureConfig
from dobeu_undertaker.utils.logging import get_logger

logger = get_logger(__name__)


class AzureDevOpsClient:
    """
    Client for Azure DevOps REST API integration.

    Handles authentication and provides methods for common
    DevOps operations like status updates and PR comments.
    """

    BASE_URL = "https://dev.azure.com"

    def __init__(self, config: AzureConfig) -> None:
        """
        Initialize the Azure DevOps client.

        Args:
            config: Azure configuration with organization and project details
        """
        self.config = config
        self.organization = config.organization
        self.project = config.project

        # Get PAT from environment
        self._pat = os.environ.get(config.pat_env_var)
        if not self._pat:
            logger.warning(
                f"Azure DevOps PAT not found in {config.pat_env_var} environment variable"
            )

        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client with authentication."""
        if self._client is None:
            import base64

            # Azure DevOps uses Basic auth with empty username and PAT as password
            auth_string = base64.b64encode(f":{self._pat}".encode()).decode()

            self._client = httpx.AsyncClient(
                base_url=f"{self.BASE_URL}/{self.organization}",
                headers={
                    "Authorization": f"Basic {auth_string}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )

        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def update_build_status(
        self,
        build_id: int,
        status: str,
        description: str,
    ) -> dict[str, Any]:
        """
        Update the status of a build.

        Args:
            build_id: The build ID to update
            status: Status string (succeeded, failed, etc.)
            description: Status description

        Returns:
            API response
        """
        client = await self._get_client()

        response = await client.patch(
            f"/{self.project}/_apis/build/builds/{build_id}",
            params={"api-version": "7.1"},
            json={
                "status": status,
                "result": status,
            },
        )
        response.raise_for_status()
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def create_pr_comment(
        self,
        repository_id: str,
        pull_request_id: int,
        content: str,
        thread_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create a comment on a pull request.

        Args:
            repository_id: Repository ID or name
            pull_request_id: Pull request ID
            content: Comment content (markdown supported)
            thread_context: Optional context for file-specific comments

        Returns:
            API response with created thread
        """
        client = await self._get_client()

        body: dict[str, Any] = {
            "comments": [{"content": content, "commentType": "text"}],
            "status": "active",
        }

        if thread_context:
            body["threadContext"] = thread_context

        response = await client.post(
            f"/{self.project}/_apis/git/repositories/{repository_id}"
            f"/pullRequests/{pull_request_id}/threads",
            params={"api-version": "7.1"},
            json=body,
        )
        response.raise_for_status()
        return response.json()

    async def create_compliance_report_comment(
        self,
        repository_id: str,
        pull_request_id: int,
        scan_results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Create a formatted compliance report comment on a PR.

        Args:
            repository_id: Repository ID or name
            pull_request_id: Pull request ID
            scan_results: List of scan results from agents

        Returns:
            API response
        """
        # Build markdown report
        lines = [
            "## 🔍 Dobeu Undertaker Compliance Report",
            "",
            "| Agent | Status | Issues |",
            "|-------|--------|--------|",
        ]

        total_issues = 0
        has_failures = False

        for result in scan_results:
            status_emoji = {
                "passed": "✅",
                "failed": "❌",
                "warning": "⚠️",
                "error": "🔴",
            }.get(result.get("status", ""), "❓")

            issue_count = len(result.get("issues", []))
            total_issues += issue_count

            if result.get("status") in ("failed", "error"):
                has_failures = True

            lines.append(
                f"| {result.get('agent_name', 'Unknown')} | "
                f"{status_emoji} {result.get('status', 'unknown').upper()} | "
                f"{issue_count} |"
            )

        lines.extend([
            "",
            f"**Total Issues:** {total_issues}",
            "",
        ])

        # Add critical issues detail
        critical_issues = []
        for result in scan_results:
            for issue in result.get("issues", []):
                if issue.get("severity") in ("critical", "high"):
                    critical_issues.append(issue)

        if critical_issues:
            lines.extend([
                "### ⚠️ Critical/High Issues",
                "",
            ])
            for issue in critical_issues[:10]:  # Limit to 10
                lines.append(
                    f"- **{issue.get('severity', 'unknown').upper()}** "
                    f"`{issue.get('file', 'unknown')}:{issue.get('line', '?')}` - "
                    f"{issue.get('message', 'No message')}"
                )

        lines.extend([
            "",
            "---",
            "*Generated by Dobeu Undertaker*",
        ])

        content = "\n".join(lines)
        return await self.create_pr_comment(repository_id, pull_request_id, content)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def create_work_item(
        self,
        work_item_type: str,
        title: str,
        description: str,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Create a work item (bug, task, etc.) in Azure Boards.

        Args:
            work_item_type: Type of work item (Bug, Task, Issue, etc.)
            title: Work item title
            description: Work item description (HTML supported)
            tags: Optional list of tags

        Returns:
            API response with created work item
        """
        client = await self._get_client()

        operations = [
            {"op": "add", "path": "/fields/System.Title", "value": title},
            {"op": "add", "path": "/fields/System.Description", "value": description},
        ]

        if tags:
            operations.append({
                "op": "add",
                "path": "/fields/System.Tags",
                "value": "; ".join(tags),
            })

        response = await client.post(
            f"/{self.project}/_apis/wit/workitems/${work_item_type}",
            params={"api-version": "7.1"},
            json=operations,
            headers={"Content-Type": "application/json-patch+json"},
        )
        response.raise_for_status()
        return response.json()

    async def report_compliance_failure(
        self,
        repository: str,
        scan_results: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """
        Create a work item for compliance failure.

        Args:
            repository: Repository name
            scan_results: List of scan results

        Returns:
            Created work item or None if no critical issues
        """
        critical_issues = []
        for result in scan_results:
            for issue in result.get("issues", []):
                if issue.get("severity") in ("critical", "high"):
                    critical_issues.append({
                        "agent": result.get("agent_name"),
                        **issue,
                    })

        if not critical_issues:
            return None

        title = f"[Compliance] {len(critical_issues)} critical/high issues in {repository}"

        description = f"""
<h2>Compliance Scan Failure</h2>
<p>Repository: <strong>{repository}</strong></p>
<p>Found {len(critical_issues)} critical/high severity issues.</p>
<h3>Issues:</h3>
<ul>
"""

        for issue in critical_issues[:20]:  # Limit to 20
            description += f"""
<li>
    <strong>[{issue.get('severity', '').upper()}]</strong>
    {issue.get('agent', 'Unknown Agent')} -
    {issue.get('file', 'unknown')}:{issue.get('line', '?')} -
    {issue.get('message', 'No message')}
</li>
"""

        description += """
</ul>
<p><em>Generated by Dobeu Undertaker</em></p>
"""

        return await self.create_work_item(
            work_item_type="Bug",
            title=title,
            description=description,
            tags=["compliance", "automated", "dobeu-undertaker"],
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_repositories(self) -> list[dict[str, Any]]:
        """
        Get all repositories in the project.

        Returns:
            List of repository information
        """
        client = await self._get_client()

        response = await client.get(
            f"/{self.project}/_apis/git/repositories",
            params={"api-version": "7.1"},
        )
        response.raise_for_status()
        return response.json().get("value", [])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_pull_requests(
        self,
        repository_id: str,
        status: str = "active",
    ) -> list[dict[str, Any]]:
        """
        Get pull requests for a repository.

        Args:
            repository_id: Repository ID or name
            status: PR status filter (active, completed, abandoned, all)

        Returns:
            List of pull requests
        """
        client = await self._get_client()

        response = await client.get(
            f"/{self.project}/_apis/git/repositories/{repository_id}/pullrequests",
            params={"api-version": "7.1", "searchCriteria.status": status},
        )
        response.raise_for_status()
        return response.json().get("value", [])
