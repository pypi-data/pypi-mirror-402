"""Tool execution implementations."""
import mcp.types as types
from typing import Optional


async def execute_list_models(client) -> types.CallToolResult:
    """Execute list_models tool"""
    try:
        result = await client.list_models()
        
        # Format output
        output_lines = ["📊 Available AI Models:\n"]
        
        for model in result.get('models', []):
            name = model['name']
            model_id = model['id']
            available = model.get('available', False)
            credits = model.get('credits', 0)
            description = model.get('description', '')
            
            status = "✅" if available else "❌"
            output_lines.append(
                f"{status} [{model_id}] {name}\n"
                f"    {description}"
            )
            output_lines.append("")
        
        summary = result.get('summary', {})
        output_lines.append(
            f"\n💡 Summary: {summary.get('available', 0)}/{summary.get('total', 0)} models available"
        )
        output_lines.append("\nUse model_id in create_diagram to specify a model.")
        
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="\n".join(output_lines))]
        )
    except Exception as e:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"❌ Error: {str(e)}")],
            isError=True
        )


async def execute_list_workspaces(client) -> types.CallToolResult:
    """Execute list_workspaces tool"""
    try:
        workspaces = await client.list_workspaces()
        
        if not workspaces:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text="No workspaces found.")]
            )
        
        output_lines = ["📁 Your Workspaces:\n"]
        for ws in workspaces:
            ws_type = "🏠 Personal" if ws.get('is_personal') else "👥 Team"
            output_lines.append(f"{ws_type} [{ws['id']}] {ws['name']}")
        
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="\n".join(output_lines))]
        )
    except Exception as e:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"❌ Error: {str(e)}")],
            isError=True
        )


async def execute_list_folders(client, workspace_id: int) -> types.CallToolResult:
    """Execute list_folders tool"""
    try:
        folders = await client.list_folders(workspace_id)
        
        if not folders:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=f"No folders in workspace {workspace_id}.")]
            )
        
        output_lines = [f"📂 Folders in workspace {workspace_id}:\n"]
        for folder in folders:
            parent_info = f" (parent: {folder['parent']})" if folder.get('parent') else ""
            output_lines.append(f"[{folder['id']}] {folder['name']}{parent_info}")
        
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="\n".join(output_lines))]
        )
    except Exception as e:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"❌ Error: {str(e)}")],
            isError=True
        )


async def execute_list_diagrams(
    client,
    workspace_id: Optional[int] = None,
    folder_id: Optional[int] = None,
    limit: int = 20
) -> types.CallToolResult:
    """Execute list_diagrams tool"""
    try:
        diagrams = await client.list_diagrams(workspace_id, folder_id, limit)
        
        if not diagrams:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text="No diagrams found.")]
            )
        
        output_lines = [f"📊 Your Diagrams (showing {len(diagrams)}):\n"]
        for diag in diagrams:
            output_lines.append(
                f"[{diag['uuid']}] {diag['title']}\n"
                f"  Type: {diag['diagram_type']} | Workspace: {diag.get('workspace')} | "
                f"Created: {diag.get('created_at', 'N/A')[:10]}"
            )
            output_lines.append("")
        
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="\n".join(output_lines))]
        )
    except Exception as e:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"❌ Error: {str(e)}")],
            isError=True
        )


async def execute_create_diagram(
    client,
    code: str,
    diagram_type: str,
    title: str,
    model_id: Optional[int] = None,
    workspace_id: Optional[int] = None,
    folder_id: Optional[int] = None,
    few_prompts: bool = False,
    guidelines: bool = True
) -> types.CallToolResult:
    """Execute create_diagram tool"""
    try:
        result = await client.create_diagram(
            code=code,
            diagram_type=diagram_type,
            title=title,
            model_id=model_id,
            workspace_id=workspace_id,
            folder_id=folder_id,
            few_prompts=few_prompts,
            guidelines=guidelines
        )
        
        message = result.get('message', '')
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=f"✅ Diagram created!\n\n"
                         f"{message}\n\n"
                         f"Title: {result['title']}\n"
                         f"Type: {result['type']}\n"
                         f"Model: {result.get('model_used', 'N/A')}\n"
                         f"UUID: {result['uuid']}\n"
                         f"URL: {result['url']}\n\n"
                         f"🔗 Open: {result['url']}"
                )
            ]
        )
    except Exception as e:
        error_msg = str(e)
        if "402" in error_msg or "insufficient_credits" in error_msg.lower():
            return types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"❌ Insufficient credits for the selected model.\n\n"
                             f"Actions:\n"
                             f"1. Use list_models to see available models\n"
                             f"2. Add your own API key at https://rapidchart.com/settings\n"
                             f"3. Use a different model with available credits"
                    )
                ],
                isError=True
            )
        
        if "503" in error_msg or "timeout" in error_msg.lower() or "service unavailable" in error_msg.lower():
            return types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"⚠️ Request timeout (503 Service Unavailable)\n\n"
                             f"The diagram is likely still being generated in the background.\n"
                             f"This happens because AI generation can take longer than Heroku's 30s router limit.\n\n"
                             f"✅ What to do:\n"
                             f"1. Run 'list_diagrams' to check if your diagram was created\n"
                             f"2. The most recent diagram should be yours\n"
                             f"3. If not there yet, wait 10-20 seconds and check again\n\n"
                             f"💡 This is a known limitation with Heroku's infrastructure."
                    )
                ],
                isError=False  # Not actually an error, diagram is likely created
            )
        
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"❌ Error: {error_msg}")],
            isError=True
        )


async def execute_get_diagram(client, diagram_id: str) -> types.CallToolResult:
    """Execute get_diagram tool"""
    try:
        diagram = await client.get_diagram(diagram_id)
        
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=f"📊 Diagram Details:\n\n"
                         f"Title: {diagram['title']}\n"
                         f"Type: {diagram['diagram_type']}\n"
                         f"UUID: {diagram['uuid']}\n"
                         f"Workspace: {diagram.get('workspace')}\n"
                         f"Folder: {diagram.get('folder') or 'Root'}\n"
                         f"Created: {diagram.get('created_at', 'N/A')[:19]}\n"
                         f"Updated: {diagram.get('updated_at', 'N/A')[:19]}"
                )
            ]
        )
    except Exception as e:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"❌ Error: {str(e)}")],
            isError=True
        )


async def execute_update_diagram(
    client,
    diagram_id: str,
    code: str,
    prompt: Optional[str] = None,
    model_id: Optional[int] = None
) -> types.CallToolResult:
    """Execute update_diagram tool"""
    try:
        result = await client.update_diagram(diagram_id, code, prompt, model_id)
        
        message = result.get('message', '')
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=f"✅ Diagram update started!\n\n"
                         f"{message}\n\n"
                         f"Title: {result['title']}\n"
                         f"UUID: {result['uuid']}\n"
                         f"URL: {result['url']}"
                )
            ]
        )
    except Exception as e:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"❌ Error: {str(e)}")],
            isError=True
        )


async def execute_delete_diagram(client, diagram_id: str) -> types.CallToolResult:
    """Execute delete_diagram tool"""
    try:
        result = await client.delete_diagram(diagram_id)
        
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=f"✅ {result.get('message', 'Diagram deleted successfully')}"
                )
            ]
        )
    except Exception as e:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"❌ Error: {str(e)}")],
            isError=True
        )


async def execute_move_diagram(
    client,
    diagram_id: str,
    workspace_id: Optional[int] = None,
    folder_id: Optional[int] = None
) -> types.CallToolResult:
    """Execute move_diagram tool"""
    try:
        result = await client.move_diagram(diagram_id, workspace_id, folder_id)
        
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=f"✅ Diagram moved successfully!\n\n"
                         f"New location:\n"
                         f"Workspace: {result.get('workspace_id', 'N/A')}\n"
                         f"Folder: {result.get('folder_id') or 'Root'}"
                )
            ]
        )
    except Exception as e:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"❌ Error: {str(e)}")],
            isError=True
        )

