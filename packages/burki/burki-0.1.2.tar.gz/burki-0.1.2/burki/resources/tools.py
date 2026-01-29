"""
Tools resource for the Burki SDK.
"""

from typing import Any, Dict, List, Optional, Union

from burki.resources.base import BaseResource
from burki.models.tool import (
    Tool,
    ToolCreate,
    ToolUpdate,
    ToolParameter,
    HTTPToolConfig,
    PythonToolConfig,
    LambdaToolConfig,
    LambdaFunction,
    LambdaDiscoveryResult,
)


class ToolsResource(BaseResource):
    """
    Resource for managing tools.

    Example:
        ```python
        # List tools
        tools = client.tools.list()

        # Create an HTTP tool
        tool = client.tools.create(
            name="check_inventory",
            tool_type="http",
            config={"method": "GET", "url": "https://api.example.com/inventory"}
        )

        # Assign to assistant
        client.tools.assign(tool_id=123, assistant_id=456)
        ```
    """

    def list(self) -> List[Tool]:
        """
        List all tools in your organization.

        Returns:
            List of Tool objects.
        """
        response = self._http.get("/api/v1/tools")

        if isinstance(response, list):
            return [Tool.model_validate(item) for item in response]
        elif isinstance(response, dict) and "items" in response:
            return [Tool.model_validate(item) for item in response["items"]]
        return []

    async def list_async(self) -> List[Tool]:
        """
        Async version of list().
        """
        response = await self._http.get_async("/api/v1/tools")

        if isinstance(response, list):
            return [Tool.model_validate(item) for item in response]
        elif isinstance(response, dict) and "items" in response:
            return [Tool.model_validate(item) for item in response["items"]]
        return []

    def get(self, tool_id: int) -> Tool:
        """
        Get a specific tool by ID.

        Args:
            tool_id: The ID of the tool.

        Returns:
            The Tool object.
        """
        response = self._http.get(f"/api/v1/tools/{tool_id}")
        return Tool.model_validate(response)

    async def get_async(self, tool_id: int) -> Tool:
        """
        Async version of get().
        """
        response = await self._http.get_async(f"/api/v1/tools/{tool_id}")
        return Tool.model_validate(response)

    def create(
        self,
        name: str,
        tool_type: str,
        description: Optional[str] = None,
        parameters: Optional[List[Union[ToolParameter, Dict[str, Any]]]] = None,
        http_config: Optional[Union[HTTPToolConfig, Dict[str, Any]]] = None,
        python_config: Optional[Union[PythonToolConfig, Dict[str, Any]]] = None,
        lambda_config: Optional[Union[LambdaToolConfig, Dict[str, Any]]] = None,
    ) -> Tool:
        """
        Create a new tool.

        Args:
            name: Name of the tool.
            tool_type: Type of tool (http, python, lambda).
            description: Optional description.
            parameters: List of tool parameters.
            http_config: Configuration for HTTP tools.
            python_config: Configuration for Python tools.
            lambda_config: Configuration for Lambda tools.

        Returns:
            The created Tool object.
        """
        data: Dict[str, Any] = {
            "name": name,
            "tool_type": tool_type,
        }

        if description:
            data["description"] = description

        if parameters:
            data["parameters"] = [
                p.model_dump() if isinstance(p, ToolParameter) else p
                for p in parameters
            ]

        if http_config:
            data["http_config"] = (
                http_config.model_dump()
                if isinstance(http_config, HTTPToolConfig)
                else http_config
            )

        if python_config:
            data["python_config"] = (
                python_config.model_dump()
                if isinstance(python_config, PythonToolConfig)
                else python_config
            )

        if lambda_config:
            data["lambda_config"] = (
                lambda_config.model_dump()
                if isinstance(lambda_config, LambdaToolConfig)
                else lambda_config
            )

        response = self._http.post("/api/v1/tools", json=data)
        return Tool.model_validate(response)

    async def create_async(
        self,
        name: str,
        tool_type: str,
        description: Optional[str] = None,
        parameters: Optional[List[Union[ToolParameter, Dict[str, Any]]]] = None,
        http_config: Optional[Union[HTTPToolConfig, Dict[str, Any]]] = None,
        python_config: Optional[Union[PythonToolConfig, Dict[str, Any]]] = None,
        lambda_config: Optional[Union[LambdaToolConfig, Dict[str, Any]]] = None,
    ) -> Tool:
        """
        Async version of create().
        """
        data: Dict[str, Any] = {
            "name": name,
            "tool_type": tool_type,
        }

        if description:
            data["description"] = description

        if parameters:
            data["parameters"] = [
                p.model_dump() if isinstance(p, ToolParameter) else p
                for p in parameters
            ]

        if http_config:
            data["http_config"] = (
                http_config.model_dump()
                if isinstance(http_config, HTTPToolConfig)
                else http_config
            )

        if python_config:
            data["python_config"] = (
                python_config.model_dump()
                if isinstance(python_config, PythonToolConfig)
                else python_config
            )

        if lambda_config:
            data["lambda_config"] = (
                lambda_config.model_dump()
                if isinstance(lambda_config, LambdaToolConfig)
                else lambda_config
            )

        response = await self._http.post_async("/api/v1/tools", json=data)
        return Tool.model_validate(response)

    def update(
        self,
        tool_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        parameters: Optional[List[Union[ToolParameter, Dict[str, Any]]]] = None,
        http_config: Optional[Union[HTTPToolConfig, Dict[str, Any]]] = None,
        python_config: Optional[Union[PythonToolConfig, Dict[str, Any]]] = None,
        lambda_config: Optional[Union[LambdaToolConfig, Dict[str, Any]]] = None,
    ) -> Tool:
        """
        Update an existing tool.

        Args:
            tool_id: The ID of the tool.
            name: New name for the tool.
            description: New description.
            is_active: Whether the tool is active.
            parameters: Updated parameters.
            http_config: Updated HTTP configuration.
            python_config: Updated Python configuration.
            lambda_config: Updated Lambda configuration.

        Returns:
            The updated Tool object.
        """
        data: Dict[str, Any] = {}

        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if is_active is not None:
            data["is_active"] = is_active
        if parameters is not None:
            data["parameters"] = [
                p.model_dump() if isinstance(p, ToolParameter) else p
                for p in parameters
            ]
        if http_config is not None:
            data["http_config"] = (
                http_config.model_dump()
                if isinstance(http_config, HTTPToolConfig)
                else http_config
            )
        if python_config is not None:
            data["python_config"] = (
                python_config.model_dump()
                if isinstance(python_config, PythonToolConfig)
                else python_config
            )
        if lambda_config is not None:
            data["lambda_config"] = (
                lambda_config.model_dump()
                if isinstance(lambda_config, LambdaToolConfig)
                else lambda_config
            )

        response = self._http.patch(f"/api/v1/tools/{tool_id}", json=data)
        return Tool.model_validate(response)

    async def update_async(
        self,
        tool_id: int,
        **kwargs: Any,
    ) -> Tool:
        """
        Async version of update().
        """
        response = await self._http.patch_async(f"/api/v1/tools/{tool_id}", json=kwargs)
        return Tool.model_validate(response)

    def delete(self, tool_id: int) -> bool:
        """
        Delete a tool.

        Args:
            tool_id: The ID of the tool.

        Returns:
            True if deleted successfully.
        """
        self._http.delete(f"/api/v1/tools/{tool_id}")
        return True

    async def delete_async(self, tool_id: int) -> bool:
        """
        Async version of delete().
        """
        await self._http.delete_async(f"/api/v1/tools/{tool_id}")
        return True

    def assign(self, tool_id: int, assistant_id: int) -> Dict[str, Any]:
        """
        Assign a tool to an assistant.

        Args:
            tool_id: The ID of the tool.
            assistant_id: The ID of the assistant.

        Returns:
            Response indicating success.
        """
        response = self._http.post(
            f"/api/v1/tools/{tool_id}/assign", json={"assistant_id": assistant_id}
        )
        return response

    async def assign_async(self, tool_id: int, assistant_id: int) -> Dict[str, Any]:
        """
        Async version of assign().
        """
        response = await self._http.post_async(
            f"/api/v1/tools/{tool_id}/assign", json={"assistant_id": assistant_id}
        )
        return response

    def unassign(self, tool_id: int, assistant_id: int) -> Dict[str, Any]:
        """
        Unassign a tool from an assistant.

        Args:
            tool_id: The ID of the tool.
            assistant_id: The ID of the assistant.

        Returns:
            Response indicating success.
        """
        response = self._http.post(
            f"/api/v1/tools/{tool_id}/unassign", json={"assistant_id": assistant_id}
        )
        return response

    async def unassign_async(self, tool_id: int, assistant_id: int) -> Dict[str, Any]:
        """
        Async version of unassign().
        """
        response = await self._http.post_async(
            f"/api/v1/tools/{tool_id}/unassign", json={"assistant_id": assistant_id}
        )
        return response

    def discover_lambda(self, region: str = "us-east-1") -> List[LambdaFunction]:
        """
        Discover AWS Lambda functions for creating Lambda tools.

        Args:
            region: AWS region to search in.

        Returns:
            List of LambdaFunction objects.
        """
        response = self._http.get(
            "/api/v1/tools/discover-lambda", params={"region": region}
        )

        if isinstance(response, list):
            return [LambdaFunction.model_validate(item) for item in response]
        elif isinstance(response, dict) and "functions" in response:
            return [
                LambdaFunction.model_validate(item) for item in response["functions"]
            ]
        return []

    async def discover_lambda_async(
        self, region: str = "us-east-1"
    ) -> List[LambdaFunction]:
        """
        Async version of discover_lambda().
        """
        response = await self._http.get_async(
            "/api/v1/tools/discover-lambda", params={"region": region}
        )

        if isinstance(response, list):
            return [LambdaFunction.model_validate(item) for item in response]
        elif isinstance(response, dict) and "functions" in response:
            return [
                LambdaFunction.model_validate(item) for item in response["functions"]
            ]
        return []
