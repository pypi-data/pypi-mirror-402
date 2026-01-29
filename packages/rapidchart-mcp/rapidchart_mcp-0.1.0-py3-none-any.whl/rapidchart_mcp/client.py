"""HTTP client for RapidChart API."""
import httpx
from typing import Dict, List, Optional, Any


class RapidChartClient:
    """Client for interacting with RapidChart API"""
    
    def __init__(self, api_url: str, api_token: str, timeout: int = 300):
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            base_url=self.api_url,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            },
            timeout=timeout,
            verify=False  # For self-signed certs in dev
        )
    
    async def list_models(self) -> Dict[str, Any]:
        """List available AI models with user's credit info"""
        response = await self.client.get("/api/mcp/models/")
        response.raise_for_status()
        return response.json()
    
    async def list_workspaces(self) -> List[Dict[str, Any]]:
        """List user's workspaces"""
        response = await self.client.get("/api/mcp/workspaces/")
        response.raise_for_status()
        return response.json()
    
    async def list_folders(self, workspace_id: int) -> List[Dict[str, Any]]:
        """List folders in a workspace"""
        response = await self.client.get(f"/api/mcp/workspaces/{workspace_id}/folders/")
        response.raise_for_status()
        return response.json()
    
    async def list_diagrams(
        self,
        workspace_id: Optional[int] = None,
        folder_id: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """List user's diagrams"""
        params = {"limit": limit}
        if workspace_id:
            params["workspace_id"] = workspace_id
        if folder_id:
            params["folder_id"] = folder_id
        
        response = await self.client.get("/api/mcp/diagrams/", params=params)
        response.raise_for_status()
        return response.json()
    
    async def create_diagram(
        self,
        code: str,
        diagram_type: str,
        title: str,
        model_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        folder_id: Optional[int] = None,
        few_prompts: bool = False,
        guidelines: bool = True
    ) -> Dict[str, Any]:
        """Create a new diagram from code"""
        response = await self.client.post(
            "/api/mcp/diagrams/create/",
            json={
                "code": code,
                "type": diagram_type,
                "title": title,
                "model_id": model_id,
                "workspace_id": workspace_id,
                "folder_id": folder_id,
                "few_prompts": few_prompts,
                "guidelines": guidelines
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def get_diagram(self, diagram_id: str) -> Dict[str, Any]:
        """Get a specific diagram"""
        response = await self.client.get(f"/api/mcp/diagrams/{diagram_id}/")
        response.raise_for_status()
        return response.json()
    
    async def update_diagram(
        self,
        diagram_id: str,
        code: str,
        prompt: Optional[str] = None,
        model_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update an existing diagram"""
        response = await self.client.put(
            f"/api/mcp/diagrams/{diagram_id}/update/",
            json={
                "code": code,
                "prompt": prompt or "Update diagram based on new code",
                "model_id": model_id
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def delete_diagram(self, diagram_id: str) -> Dict[str, str]:
        """Delete a diagram"""
        response = await self.client.delete(f"/api/mcp/diagrams/{diagram_id}/delete/")
        response.raise_for_status()
        return response.json()
    
    async def move_diagram(
        self,
        diagram_id: str,
        workspace_id: Optional[int] = None,
        folder_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Move diagram to different folder/workspace"""
        response = await self.client.patch(
            f"/api/mcp/diagrams/{diagram_id}/move/",
            json={
                "workspace_id": workspace_id,
                "folder_id": folder_id
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

