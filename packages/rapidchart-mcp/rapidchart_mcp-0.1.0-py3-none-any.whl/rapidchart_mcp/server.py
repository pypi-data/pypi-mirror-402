"""Main MCP server implementation."""
import asyncio
import sys
from mcp.server import Server
import mcp.types as types

from .config import Config
from .client import RapidChartClient
from .tools.definitions import get_tools
from .tools import executors


class RapidChartMCPServer:
    """RapidChart MCP Server"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = RapidChartClient(
            api_url=config.api_url,
            api_token=config.api_token,
            timeout=config.timeout
        )
        self.server = Server("rapidchart")
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> list[types.Tool]:
            """List available tools"""
            return get_tools()
        
        @self.server.call_tool()
        async def call_tool(
            name: str,
            arguments: dict
        ) -> types.CallToolResult:
            """Execute a tool"""
            
            # Apply config defaults for create_diagram
            if name == "create_diagram":
                arguments.setdefault("diagram_type", self.config.default_diagram_type)
                arguments.setdefault("model_id", self.config.default_model_id)
                arguments.setdefault("few_prompts", self.config.few_prompts)
                arguments.setdefault("guidelines", self.config.guidelines)
            
            # Route to appropriate tool executor
            try:
                if name == "list_models":
                    return await executors.execute_list_models(self.client)
                
                elif name == "list_workspaces":
                    return await executors.execute_list_workspaces(self.client)
                
                elif name == "list_folders":
                    return await executors.execute_list_folders(
                        self.client,
                        workspace_id=arguments["workspace_id"]
                    )
                
                elif name == "list_diagrams":
                    return await executors.execute_list_diagrams(
                        self.client,
                        workspace_id=arguments.get("workspace_id"),
                        folder_id=arguments.get("folder_id"),
                        limit=arguments.get("limit", 20)
                    )
                
                elif name == "create_diagram":
                    return await executors.execute_create_diagram(
                        self.client,
                        code=arguments["code"],
                        diagram_type=arguments["diagram_type"],
                        title=arguments["title"],
                        model_id=arguments.get("model_id"),
                        workspace_id=arguments.get("workspace_id"),
                        folder_id=arguments.get("folder_id"),
                        few_prompts=arguments.get("few_prompts", False),
                        guidelines=arguments.get("guidelines", True)
                    )
                
                elif name == "get_diagram":
                    return await executors.execute_get_diagram(
                        self.client,
                        diagram_id=arguments["diagram_id"]
                    )
                
                elif name == "update_diagram":
                    return await executors.execute_update_diagram(
                        self.client,
                        diagram_id=arguments["diagram_id"],
                        code=arguments["code"],
                        prompt=arguments.get("prompt"),
                        model_id=arguments.get("model_id")
                    )
                
                elif name == "delete_diagram":
                    return await executors.execute_delete_diagram(
                        self.client,
                        diagram_id=arguments["diagram_id"]
                    )
                
                elif name == "move_diagram":
                    return await executors.execute_move_diagram(
                        self.client,
                        diagram_id=arguments["diagram_id"],
                        workspace_id=arguments.get("workspace_id"),
                        folder_id=arguments.get("folder_id")
                    )
                
                else:
                    return types.CallToolResult(
                        content=[types.TextContent(type="text", text=f"Unknown tool: {name}")],
                        isError=True
                    )
            
            except Exception as e:
                return types.CallToolResult(
                    content=[types.TextContent(type="text", text=f"Error executing {name}: {str(e)}")],
                    isError=True
                )
    
    async def run(self):
        """Run the MCP server"""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.client.close()


async def main():
    """Main entry point"""
    try:
        config = Config.from_env()
    except ValueError as e:
        print(f"❌ Configuration error: {e}", file=sys.stderr)
        print("\nRequired environment variable: RAPIDCHART_API_TOKEN", file=sys.stderr)
        print("Get your token at: https://rapidchart.com/settings", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1
    
    server = RapidChartMCPServer(config)
    
    try:
        await server.run()
    finally:
        await server.cleanup()
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

