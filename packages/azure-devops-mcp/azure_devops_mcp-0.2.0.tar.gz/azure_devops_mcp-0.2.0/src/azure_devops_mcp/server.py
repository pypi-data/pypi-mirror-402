"""
Azure DevOps MCP Server
Provides tools for interacting with Azure DevOps work items
"""

import asyncio
import logging
import os
import sys
from typing import Any

import yaml
from dotenv import load_dotenv
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from .azure_devops_client import AzureDevOpsClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global client instance
client: AzureDevOpsClient | None = None


def load_config() -> dict:
    """Load configuration from config.yaml or environment variables"""
    # Try to find config.yaml in multiple locations
    config_paths = [
        # 1. Package data location (when installed via pip)
        os.path.join(os.path.dirname(__file__), "config.yaml"),
        # 2. Project root relative to source (development)
        os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml"),
        # 3. Current working directory
        os.path.join(os.getcwd(), "config.yaml"),
    ]

    for config_path in config_paths:
        try:
            with open(config_path, "r") as f:
                logger.info(f"Loading config from {config_path}")
                return yaml.safe_load(f)
        except FileNotFoundError:
            continue

    logger.warning("Config file not found, using environment variables")

    # Detect auth method based on available environment variables
    auth_method = "pat"  # Use PAT for TFS

    auth_config = {"method": auth_method}
    if auth_method == "pat":
        auth_config["pat"] = os.getenv("AZURE_DEVOPS_PAT")
    elif auth_method == "basic":
        auth_config["username"] = os.getenv("TFS_USERNAME")
        auth_config["password"] = os.getenv("TFS_PASSWORD")
    else:
        # OAuth configuration
        auth_config["oauth"] = {
            "client_id": os.getenv("AZURE_CLIENT_ID"),
            "client_secret": os.getenv("AZURE_CLIENT_SECRET"),
            "tenant_id": os.getenv("AZURE_TENANT_ID"),
        }

    config = {
        "organization": {
            "url": os.getenv("AZURE_DEVOPS_ORG_URL"),
            "project": os.getenv("AZURE_DEVOPS_PROJECT"),
        },
        "auth": auth_config,
    }

    # Validate required configuration
    org_url = config["organization"]["url"]
    project = config["organization"]["project"]
    pat = config["auth"].get("pat") if auth_method == "pat" else config["auth"].get("username")

    if not org_url:
        raise ValueError(
            "AZURE_DEVOPS_ORG_URL environment variable is required. "
            "Set it to your Azure DevOps/TFS organization URL."
        )
    if not project:
        raise ValueError(
            "AZURE_DEVOPS_PROJECT environment variable is required. "
            "Set it to your default project name."
        )
    if auth_method == "pat" and not pat:
        raise ValueError(
            "AZURE_DEVOPS_PAT environment variable is required. "
            "Set it to your Personal Access Token."
        )

    return config


def initialize_client():
    """Initialize Azure DevOps client"""
    global client
    config = load_config()

    client = AzureDevOpsClient(
        org_url=config["organization"]["url"],
        project=config["organization"]["project"],
        auth_config=config["auth"],
    )
    logger.info("Azure DevOps client initialized")


# Create server instance
server = Server("azure-devops-mcp")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="get_work_item",
            description="Get a single work item by ID. Returns all available fields including title, state, assigned user, description, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_item_id": {
                        "type": "integer",
                        "description": "The work item ID (e.g., 12345)",
                    },
                    "project": {
                        "type": "string",
                        "description": "Project name (optional, uses default from config if not specified)",
                    },
                },
                "required": ["work_item_id"],
            },
        ),
        Tool(
            name="get_work_items",
            description="Get multiple work items by a list of IDs. Useful for fetching details for multiple work items at once.",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_item_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of work item IDs (e.g., [12345, 12346, 12347])",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of fields to retrieve (e.g., ['System.Id', 'System.Title', 'System.State']). If not specified, returns all default fields.",
                    },
                    "project": {
                        "type": "string",
                        "description": "Project name (optional, uses default from config if not specified)",
                    },
                },
                "required": ["work_item_ids"],
            },
        ),
        Tool(
            name="query_work_items",
            description="Query work items using WIQL (Work Item Query Language). This is a powerful tool for complex queries. Example queries: 'SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = @project AND [System.State] = 'Active''",
            inputSchema={
                "type": "object",
                "properties": {
                    "wiql": {
                        "type": "string",
                        "description": "WIQL query string. Use @project as a placeholder for the project name.",
                    },
                    "project": {
                        "type": "string",
                        "description": "Project name (optional, uses default from config if not specified)",
                    },
                },
                "required": ["wiql"],
            },
        ),
        Tool(
            name="create_work_item",
            description="Create a new work item (Bug, Task, User Story, Feature, etc.). You can specify title, description, assigned user, and additional fields.",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_item_type": {
                        "type": "string",
                        "description": "Type of work item to create (e.g., 'Bug', 'Task', 'User Story', 'Feature', 'Epic')",
                        "enum": ["Bug", "Task", "User Story", "Feature", "Epic", "Issue", "Test Case"],
                    },
                    "title": {
                        "type": "string",
                        "description": "Title of the work item",
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the work item (supports HTML formatting)",
                    },
                    "assigned_to": {
                        "type": "string",
                        "description": "Email address of the user to assign this work item to",
                    },
                    "fields": {
                        "type": "object",
                        "description": "Additional fields to set (e.g., {'System.Priority': '1', 'Microsoft.VSTS.Common.Severity': 'High'})",
                    },
                    "project": {
                        "type": "string",
                        "description": "Project name (optional, uses default from config if not specified)",
                    },
                },
                "required": ["work_item_type", "title"],
            },
        ),
        Tool(
            name="search_work_items",
            description="Search work items by text in title or description. Returns a list of matching work items ordered by last changed date.",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_text": {
                        "type": "string",
                        "description": "Text to search for in work item titles and descriptions",
                    },
                    "project": {
                        "type": "string",
                        "description": "Project name (optional, uses default from config if not specified)",
                    },
                    "top": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 100)",
                    },
                },
                "required": ["search_text"],
            },
        ),
        Tool(
            name="get_projects",
            description="Get a list of all projects in the Azure DevOps organization",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_work_item_types",
            description="Get available work item types for a project. Useful to see what types of work items you can create.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {
                        "type": "string",
                        "description": "Project name (optional, uses default from config if not specified)",
                    },
                },
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls"""
    if client is None:
        initialize_client()

    if arguments is None:
        arguments = {}

    try:
        if name == "get_work_item":
            work_item_id = arguments.get("work_item_id")
            project = arguments.get("project")
            result = await client.get_work_item(work_item_id, project)
            return [TextContent(type="text", text=format_work_item(result))]

        elif name == "get_work_items":
            work_item_ids = arguments.get("work_item_ids", [])
            fields = arguments.get("fields")
            project = arguments.get("project")
            results = await client.get_work_items(work_item_ids, fields, project)
            return [TextContent(type="text", text=format_work_items(results))]

        elif name == "query_work_items":
            wiql = arguments.get("wiql", "")
            project = arguments.get("project")
            # Replace @project placeholder if present
            if project and "@project" in wiql:
                wiql = wiql.replace("@project", project)
            result = await client.query_work_items(wiql, project)
            return [TextContent(type="text", text=format_query_result(result))]

        elif name == "create_work_item":
            work_item_type = arguments.get("work_item_type")
            title = arguments.get("title")
            description = arguments.get("description")
            assigned_to = arguments.get("assigned_to")
            fields = arguments.get("fields")
            project = arguments.get("project")
            result = await client.create_work_item(
                work_item_type=work_item_type,
                title=title,
                description=description,
                assigned_to=assigned_to,
                fields=fields,
                project=project,
            )
            return [TextContent(type="text", text=f"Work item created successfully:\n\n{format_work_item(result)}")]

        elif name == "search_work_items":
            search_text = arguments.get("search_text", "")
            project = arguments.get("project")
            top = arguments.get("top", 100)
            results = await client.search_work_items(search_text, project, top)
            return [TextContent(type="text", text=format_work_items(results))]

        elif name == "get_projects":
            projects = await client.get_projects()
            return [TextContent(type="text", text=format_projects(projects))]

        elif name == "get_work_item_types":
            project = arguments.get("project")
            types = await client.get_work_item_types(project)
            return [TextContent(type="text", text=f"Available work item types:\n\n" + "\n".join(f"- {t}" for t in types))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


def format_work_item(work_item: dict) -> str:
    """Format a single work item for display"""
    fields = work_item.get("fields", {})

    output = f"Work Item #{fields.get('System.Id', 'N/A')}\n"
    output += f"{'=' * 50}\n"
    output += f"Type: {fields.get('System.WorkItemType', 'N/A')}\n"
    output += f"Title: {fields.get('System.Title', 'N/A')}\n"
    output += f"State: {fields.get('System.State', 'N/A')}\n"
    output += f"Assigned To: {fields.get('System.AssignedTo', 'Unassigned')}\n"
    output += f"Created: {fields.get('System.CreatedDate', 'N/A')}\n"
    output += f"Changed: {fields.get('System.ChangedDate', 'N/A')}\n"
    output += f"Priority: {fields.get('System.Priority', 'N/A')}\n"

    if description := fields.get('System.Description'):
        # Strip HTML tags for cleaner display
        import re
        clean_desc = re.sub(r'<[^>]+>', '', description)
        output += f"\nDescription:\n{clean_desc[:500]}...\n"

    if tags := fields.get('System.Tags'):
        output += f"\nTags: {tags}\n"

    return output


def format_work_items(work_items: list[dict]) -> str:
    """Format multiple work items for display"""
    if not work_items:
        return "No work items found."

    output = f"Found {len(work_items)} work item(s):\n\n"

    for item in work_items:
        fields = item.get("fields", {})
        output += f"#{fields.get('System.Id', 'N/A')} - [{fields.get('System.WorkItemType', 'N/A')}] "
        output += f"{fields.get('System.Title', 'N/A')}\n"
        output += f"  State: {fields.get('System.State', 'N/A')} | "
        output += f"Assigned: {fields.get('System.AssignedTo', 'Unassigned')}\n\n"

    return output


def format_query_result(result: dict) -> str:
    """Format query result for display"""
    work_items = result.get("workItems", [])

    if not work_items:
        return "Query returned no results."

    output = f"Query returned {len(work_items)} work item(s):\n\n"
    for item in work_items:
        output += f"#{item['id']}\n"

    output += "\nUse get_work_items with these IDs to get full details."

    return output


def format_projects(projects: list[dict]) -> str:
    """Format projects list for display"""
    if not projects:
        return "No projects found."

    output = f"Found {len(projects)} project(s):\n\n"
    for project in projects:
        output += f"- {project['name']} (ID: {project['id']})\n"
        output += f"  State: {project['state']}\n"
        output += f"  URL: {project['url']}\n\n"

    return output


async def main():
    """Main entry point"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="azure-devops-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def entry_point() -> int:
    """Synchronous entry point for console_scripts"""
    try:
        asyncio.run(main())
        return 0
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(entry_point())
