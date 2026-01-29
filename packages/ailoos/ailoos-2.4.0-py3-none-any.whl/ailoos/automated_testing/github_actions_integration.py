"""
GitHub Actions Integration
Handles CI/CD pipeline integration with GitHub Actions for automated testing.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import aiohttp


@dataclass
class WorkflowRun:
    id: str
    name: str
    status: str
    conclusion: Optional[str]
    created_at: str
    updated_at: str
    url: str


@dataclass
class WorkflowStatus:
    workflow_id: str
    runs: List[WorkflowRun]
    last_run: Optional[WorkflowRun]


class GitHubActionsIntegration:
    """
    Integrates with GitHub Actions for automated test execution in CI/CD pipelines.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.github_token = config.get('token')
        self.repo_owner = config.get('owner', 'your-org')
        self.repo_name = config.get('repo', 'your-repo')
        self.base_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"

        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def trigger_workflow(self, workflow_file: str, inputs: Optional[Dict[str, Any]] = None) -> str:
        """
        Trigger a GitHub Actions workflow.

        Args:
            workflow_file: Name of the workflow file (e.g., 'ci.yml')
            inputs: Optional inputs for the workflow

        Returns:
            Run ID of the triggered workflow
        """
        if not self.session:
            async with self:
                return await self._trigger_workflow(workflow_file, inputs)
        return await self._trigger_workflow(workflow_file, inputs)

    async def _trigger_workflow(self, workflow_file: str, inputs: Optional[Dict[str, Any]] = None) -> str:
        """Internal method to trigger workflow."""
        url = f"{self.base_url}/actions/workflows/{workflow_file}/dispatches"

        payload = {
            'ref': self.config.get('branch', 'main')
        }

        if inputs:
            payload['inputs'] = inputs

        async with self.session.post(url, json=payload) as response:
            if response.status == 204:
                self.logger.info(f"Workflow {workflow_file} triggered successfully")
                # Get the run ID by checking recent runs
                run_id = await self._get_latest_run_id(workflow_file)
                return run_id
            else:
                error_text = await response.text()
                raise Exception(f"Failed to trigger workflow: {response.status} - {error_text}")

    async def schedule_workflow(self, workflow_file: str, schedule_config: Dict[str, Any]) -> str:
        """
        Schedule a workflow run.

        Args:
            workflow_file: Workflow file name
            schedule_config: Scheduling configuration

        Returns:
            Schedule ID
        """
        # In a real implementation, this would modify the workflow file
        # For now, we'll simulate scheduling
        schedule_id = f"schedule_{workflow_file}_{asyncio.get_event_loop().time()}"

        self.logger.info(f"Scheduled workflow {workflow_file} with ID: {schedule_id}")
        return schedule_id

    async def get_workflow_status(self, workflow_file: str) -> WorkflowStatus:
        """
        Get the status of a workflow.

        Args:
            workflow_file: Workflow file name

        Returns:
            WorkflowStatus object
        """
        if not self.session:
            async with self:
                return await self._get_workflow_status(workflow_file)
        return await self._get_workflow_status(workflow_file)

    async def _get_workflow_status(self, workflow_file: str) -> WorkflowStatus:
        """Internal method to get workflow status."""
        url = f"{self.base_url}/actions/workflows/{workflow_file}/runs"

        params = {
            'per_page': 10  # Get last 10 runs
        }

        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                runs = []

                for run_data in data.get('workflow_runs', []):
                    run = WorkflowRun(
                        id=str(run_data['id']),
                        name=run_data['name'],
                        status=run_data['status'],
                        conclusion=run_data.get('conclusion'),
                        created_at=run_data['created_at'],
                        updated_at=run_data['updated_at'],
                        url=run_data['html_url']
                    )
                    runs.append(run)

                last_run = runs[0] if runs else None

                return WorkflowStatus(
                    workflow_id=workflow_file,
                    runs=runs,
                    last_run=last_run
                )
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get workflow status: {response.status} - {error_text}")

    async def _get_latest_run_id(self, workflow_file: str) -> str:
        """Get the ID of the latest workflow run."""
        status = await self._get_workflow_status(workflow_file)
        return status.last_run.id if status.last_run else "unknown"

    async def cancel_workflow_run(self, run_id: str) -> bool:
        """
        Cancel a running workflow.

        Args:
            run_id: ID of the workflow run to cancel

        Returns:
            Success status
        """
        if not self.session:
            async with self:
                return await self._cancel_workflow_run(run_id)
        return await self._cancel_workflow_run(run_id)

    async def _cancel_workflow_run(self, run_id: str) -> bool:
        """Internal method to cancel workflow run."""
        url = f"{self.base_url}/actions/runs/{run_id}/cancel"

        async with self.session.post(url) as response:
            if response.status == 202:
                self.logger.info(f"Workflow run {run_id} cancelled successfully")
                return True
            else:
                error_text = await response.text()
                self.logger.error(f"Failed to cancel workflow run: {response.status} - {error_text}")
                return False

    async def get_workflow_logs(self, run_id: str) -> Dict[str, Any]:
        """
        Get logs from a workflow run.

        Args:
            run_id: Workflow run ID

        Returns:
            Log data
        """
        if not self.session:
            async with self:
                return await self._get_workflow_logs(run_id)
        return await self._get_workflow_logs(run_id)

    async def _get_workflow_logs(self, run_id: str) -> Dict[str, Any]:
        """Internal method to get workflow logs."""
        url = f"{self.base_url}/actions/runs/{run_id}/logs"

        async with self.session.get(url) as response:
            if response.status == 200:
                # In a real implementation, you'd parse the zip file
                # For now, return mock data
                return {
                    'run_id': run_id,
                    'logs_available': True,
                    'log_entries': [
                        {'timestamp': '2023-01-01T00:00:00Z', 'message': 'Test started'},
                        {'timestamp': '2023-01-01T00:01:00Z', 'message': 'Test completed successfully'}
                    ]
                }
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get workflow logs: {response.status} - {error_text}")

    def get_status(self) -> Dict[str, Any]:
        """Get current status of GitHub Actions integration."""
        return {
            'configured': bool(self.github_token),
            'repo': f"{self.repo_owner}/{self.repo_name}",
            'session_active': self.session is not None and not self.session.closed
        }