"""
Azure DevOps API Client
Handles authentication and API calls to Azure DevOps
"""

import aiohttp
import logging
import base64
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AzureDevOpsClient:
    """Client for interacting with Azure DevOps/TFS REST API"""

    def __init__(self, org_url: str, project: str, auth_config: dict):
        """
        Initialize Azure DevOps client

        Args:
            org_url: Azure DevOps/TFS organization URL
            project: Default project name
            auth_config: Authentication configuration
        """
        self.org_url = org_url.rstrip("/")
        self.project = project
        self.auth_config = auth_config
        self._auth_method = auth_config.get("method", "basic")

        # API version - use 3.2 for TFS 2018 compatibility
        self.api_version = auth_config.get("api_version", "3.2")

    def _get_auth_header(self) -> str:
        """Get authorization header based on auth method"""
        if self._auth_method == "basic":
            # Basic authentication with username and password
            username = self.auth_config.get("username", "")
            password = self.auth_config.get("password", "")
            credentials = f"{username}:{password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            return f"Basic {encoded}"

        elif self._auth_method == "pat":
            # PAT token authentication
            pat = self.auth_config.get("pat", "")
            return f"Basic {base64.b64encode(f":{pat}".encode()).decode()}"

        elif self._auth_method == "bearer":
            # Bearer token (OAuth)
            return f"Bearer {self.auth_config.get('access_token', '')}"

        else:
            raise ValueError(f"Unsupported auth method: {self._auth_method}")

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests"""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": self._get_auth_header(),
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        project: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Make HTTP request to Azure DevOps/TFS API

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data
            project: Project name (overrides default)

        Returns:
            Response data as dictionary
        """
        url = f"{self.org_url}/{endpoint}"
        headers = self._get_headers()

        # Set API version if not provided in params
        if params is None:
            params = {}
        if "api-version" not in params:
            params["api-version"] = self.api_version

        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=data,
                ) as response:
                    response.raise_for_status()
                    return await response.json()

            except aiohttp.ClientResponseError as e:
                logger.error(f"API request failed: {e}")
                error_text = await e.response.text()
                raise Exception(f"TFS API error: {e.status} - {error_text}")

            except Exception as e:
                logger.error(f"Request failed: {e}")
                raise

    async def get_work_item(self, work_item_id: int, project: Optional[str] = None) -> dict[str, Any]:
        """
        Get a single work item by ID

        Args:
            work_item_id: Work item ID
            project: Project name (optional)

        Returns:
            Work item data
        """
        endpoint = f"_apis/wit/workitems/{work_item_id}"
        return await self._request("GET", endpoint, project=project)

    async def get_work_items(
        self,
        work_item_ids: list[int],
        fields: Optional[list[str]] = None,
        project: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Get multiple work items by IDs

        Args:
            work_item_ids: List of work item IDs
            fields: List of fields to retrieve
            project: Project name (optional)

        Returns:
            List of work items
        """
        endpoint = "_apis/wit/workitems"
        params = {"ids": ",".join(map(str, work_item_ids))}
        if fields:
            params["fields"] = ",".join(fields)

        result = await self._request("GET", endpoint, params=params, project=project)
        return result.get("value", [])

    async def query_work_items(
        self,
        wiql: str,
        project: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Query work items using WIQL (Work Item Query Language)

        Args:
            wiql: WIQL query string
            project: Project name (optional)

        Returns:
            Query results with work item IDs
        """
        endpoint = "_apis/wit/wiql"
        data = {"query": wiql}

        return await self._request("POST", endpoint, data=data, project=project)

    async def create_work_item(
        self,
        work_item_type: str,
        title: str,
        description: Optional[str] = None,
        assigned_to: Optional[str] = None,
        fields: Optional[dict[str, str]] = None,
        project: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a new work item

        Args:
            work_item_type: Type of work item (Bug, Task, User Story, etc.)
            title: Work item title
            description: Work item description (HTML format)
            assigned_to: Email or name of assigned user
            fields: Additional fields to set
            project: Project name (optional)

        Returns:
            Created work item data
        """
        project_name = project or self.project
        endpoint = f"{project_name}/_apis/wit/workitems/${work_item_type}"

        # Build document for PATCH request
        document = [
            {"op": "add", "path": "/fields/System.Title", "value": title},
        ]

        if description:
            document.append({
                "op": "add",
                "path": "/fields/System.Description",
                "value": description,
            })

        if assigned_to:
            document.append({
                "op": "add",
                "path": "/fields/System.AssignedTo",
                "value": assigned_to,
            })

        if fields:
            for field_path, field_value in fields.items():
                document.append({
                    "op": "add",
                    "path": f"/fields/{field_path}",
                    "value": field_value,
                })

        # For PATCH requests, we need special handling
        url = f"{self.org_url}/{endpoint}"
        headers = self._get_headers()

        async with aiohttp.ClientSession() as session:
            try:
                async with session.patch(
                    url=url,
                    headers=headers,
                    params={"api-version": self.api_version},
                    json=document,
                ) as response:
                    response.raise_for_status()
                    return await response.json()

            except aiohttp.ClientResponseError as e:
                error_text = await e.response.text()
                raise Exception(f"Failed to create work item: {e.status} - {error_text}")

    async def search_work_items(
        self,
        search_text: str,
        project: Optional[str] = None,
        top: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Search work items by text

        Args:
            search_text: Text to search for
            project: Project name (optional)
            top: Maximum number of results

        Returns:
            List of matching work items
        """
        project_name = project or self.project

        # Build WIQL search query
        wiql = f"""
        SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType]
        FROM WorkItems
        WHERE [System.TeamProject] = '{project_name}'
        AND (CONTAINS([System.Title], '{search_text}')
             OR CONTAINS([System.Description], '{search_text}'))
        ORDER BY [System.ChangedDate] DESC
        """

        result = await self.query_work_items(wiql, project)

        # Get work item IDs from query result
        work_item_ids = [item["id"] for item in result.get("workItems", [])[:top]]

        if not work_item_ids:
            return []

        # Fetch full work item details
        return await self.get_work_items(work_item_ids, project=project)

    async def get_projects(self) -> list[dict[str, Any]]:
        """
        Get list of all projects

        Returns:
            List of projects
        """
        endpoint = "_apis/projects"
        result = await self._request("GET", endpoint)
        return result.get("value", [])

    async def get_work_item_types(self, project: Optional[str] = None) -> list[str]:
        """
        Get available work item types for a project

        Args:
            project: Project name (optional)

        Returns:
            List of work item type names
        """
        project_name = project or self.project
        endpoint = f"{project_name}/_apis/wit/workitemtypes"
        result = await self._request("GET", endpoint)
        return [item["name"] for item in result.get("value", [])]
