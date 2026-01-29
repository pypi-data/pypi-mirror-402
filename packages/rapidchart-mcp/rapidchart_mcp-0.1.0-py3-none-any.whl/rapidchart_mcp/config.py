"""Configuration management for RapidChart MCP server."""
import os
from typing import Optional
from pydantic import BaseModel, Field


class Config(BaseModel):
    """MCP Server Configuration"""
    api_token: str = Field(..., description="RapidChart API token")
    api_url: str = Field(
        default="https://fastuml-0bb6938ba599.herokuapp.com",
        description="RapidChart API base URL"
    )
    default_diagram_type: str = Field(
        default="general",
        description="Default diagram type"
    )
    default_model_id: Optional[int] = Field(
        default=None,
        description="Default model ID (null = backend default)"
    )
    few_prompts: bool = Field(
        default=False,
        description="Enable multi-step thinking by default"
    )
    guidelines: bool = Field(
        default=True,
        description="Include diagram guidelines by default"
    )
    timeout: int = Field(
        default=300,
        description="Request timeout in seconds"
    )

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        api_token = os.environ.get("RAPIDCHART_API_TOKEN")
        if not api_token:
            raise ValueError(
                "RAPIDCHART_API_TOKEN environment variable is required. "
                "Get your token at https://rapidchart.com/settings"
            )
        
        return cls(
            api_token=api_token,
            api_url=os.getenv(
                "RAPIDCHART_API_URL",
                "https://fastuml-0bb6938ba599.herokuapp.com"
            ),
            default_diagram_type=os.getenv("RAPIDCHART_DEFAULT_TYPE", "general"),
            default_model_id=int(os.getenv("RAPIDCHART_DEFAULT_MODEL")) if os.getenv("RAPIDCHART_DEFAULT_MODEL") else None,
            few_prompts=os.getenv("RAPIDCHART_FEW_PROMPTS", "false").lower() == "true",
            guidelines=os.getenv("RAPIDCHART_GUIDELINES", "true").lower() == "true",
            timeout=int(os.getenv("RAPIDCHART_TIMEOUT", "300"))
        )



