"""Tool definitions and implementations for RapidChart MCP."""
import mcp.types as types
from typing import Optional


# Tool definitions
TOOLS = [
    types.Tool(
        name="list_models",
        description="List all available AI models with your current credit status and access info",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
    types.Tool(
        name="list_workspaces",
        description="List all workspaces you have access to",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
    types.Tool(
        name="list_folders",
        description="List all folders in a specific workspace",
        inputSchema={
            "type": "object",
            "properties": {
                "workspace_id": {
                    "type": "integer",
                    "description": "ID of the workspace to list folders from"
                }
            },
            "required": ["workspace_id"]
        }
    ),
    types.Tool(
        name="list_diagrams",
        description="List your diagrams with optional filters",
        inputSchema={
            "type": "object",
            "properties": {
                "workspace_id": {
                    "type": "integer",
                    "description": "Filter by workspace ID (optional)"
                },
                "folder_id": {
                    "type": "integer",
                    "description": "Filter by folder ID (optional)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of diagrams to return",
                    "default": 20
                }
            },
            "required": []
        }
    ),
    types.Tool(
        name="create_diagram",
        description="Generate a RapidChart diagram from source code. Supports multiple diagram types (class, ER, sequence, architecture, etc.) and AI models.",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Source code to analyze and generate diagram from"
                },
                "diagram_type": {
                    "type": "string",
                    "enum": [
                        "general", "class", "er", "sequence", "usecase",
                        "userflow", "c4", "aws", "azure", "google"
                    ],
                    "description": "Type of diagram to generate",
                    "default": "general"
                },
                "title": {
                    "type": "string",
                    "description": "Title for the diagram"
                },
                "model_id": {
                    "type": "integer",
                    "description": "AI model ID (optional). Use list_models to see available models."
                },
                "workspace_id": {
                    "type": "integer",
                    "description": "Workspace ID to create diagram in (optional, defaults to personal workspace)"
                },
                "folder_id": {
                    "type": "integer",
                    "description": "Folder ID to create diagram in (optional, null = root)"
                },
                "few_prompts": {
                    "type": "boolean",
                    "description": "Enable multi-step thinking for better quality (slower)",
                    "default": False
                },
                "guidelines": {
                    "type": "boolean",
                    "description": "Include diagram-specific guidelines",
                    "default": True
                }
            },
            "required": ["code", "diagram_type", "title"]
        }
    ),
    types.Tool(
        name="get_diagram",
        description="Get details of a specific diagram by its UUID",
        inputSchema={
            "type": "object",
            "properties": {
                "diagram_id": {
                    "type": "string",
                    "description": "UUID of the diagram"
                }
            },
            "required": ["diagram_id"]
        }
    ),
    types.Tool(
        name="update_diagram",
        description="Update an existing diagram with new code. The AI will regenerate the diagram with awareness of the old structure.",
        inputSchema={
            "type": "object",
            "properties": {
                "diagram_id": {
                    "type": "string",
                    "description": "UUID of the diagram to update"
                },
                "code": {
                    "type": "string",
                    "description": "New source code"
                },
                "prompt": {
                    "type": "string",
                    "description": "Optional update prompt/description",
                    "default": "Update diagram based on new code"
                },
                "model_id": {
                    "type": "integer",
                    "description": "AI model ID (optional)"
                }
            },
            "required": ["diagram_id", "code"]
        }
    ),
    types.Tool(
        name="delete_diagram",
        description="Delete a diagram permanently",
        inputSchema={
            "type": "object",
            "properties": {
                "diagram_id": {
                    "type": "string",
                    "description": "UUID of the diagram to delete"
                }
            },
            "required": ["diagram_id"]
        }
    ),
    types.Tool(
        name="move_diagram",
        description="Move a diagram to a different folder or workspace",
        inputSchema={
            "type": "object",
            "properties": {
                "diagram_id": {
                    "type": "string",
                    "description": "UUID of the diagram to move"
                },
                "workspace_id": {
                    "type": "integer",
                    "description": "Target workspace ID (optional)"
                },
                "folder_id": {
                    "type": "integer",
                    "description": "Target folder ID (optional, null for root)"
                }
            },
            "required": ["diagram_id"]
        }
    )
]


def get_tools() -> list[types.Tool]:
    """Return all available tools"""
    return TOOLS

