"""
Base MCP Server implementation for Umbra Educational Platform
Provides foundation for educational content, analytics, and assessment servers.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from src.core.logging_config import setup_logging

logger = setup_logging(__name__)


class MCPResourceType(Enum):
    """Types of MCP resources available in the educational platform."""
    COURSE = "course"
    USER_PROGRESS = "user_progress"
    ASSESSMENT = "assessment"
    RECOMMENDATION = "recommendation"
    ANALYTICS = "analytics"
    LEARNING_PATH = "learning_path"


@dataclass
class MCPResource:
    """Represents an MCP resource with metadata."""
    uri: str
    name: str
    description: str
    mime_type: str
    resource_type: MCPResourceType
    metadata: Dict[str, Any]
    last_modified: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert resource to dictionary format."""
        data = asdict(self)
        data['resource_type'] = self.resource_type.value
        data['last_modified'] = self.last_modified.isoformat()
        return data


@dataclass
class MCPTool:
    """Represents an MCP tool for data processing."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary format."""
        return asdict(self)


class BaseMCPServer(ABC):
    """
    Base class for MCP servers in the educational platform.
    Provides common functionality for resource management and tool execution.
    """
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.resources: Dict[str, MCPResource] = {}
        self.tools: Dict[str, MCPTool] = {}
        self.logger = setup_logging(f"{__name__}.{name}")
        
    async def initialize(self) -> None:
        """Initialize the MCP server."""
        self.logger.info(f"Initializing MCP server: {self.name} v{self.version}")
        await self._load_resources()
        await self._register_tools()
        self.logger.info(f"MCP server {self.name} initialized successfully")
    
    @abstractmethod
    async def _load_resources(self) -> None:
        """Load available resources. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def _register_tools(self) -> None:
        """Register available tools. Must be implemented by subclasses."""
        pass
    
    def add_resource(self, resource: MCPResource) -> None:
        """Add a resource to the server."""
        self.resources[resource.uri] = resource
        self.logger.debug(f"Added resource: {resource.uri}")
    
    def add_tool(self, tool: MCPTool) -> None:
        """Add a tool to the server."""
        self.tools[tool.name] = tool
        self.logger.debug(f"Added tool: {tool.name}")
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List all available resources."""
        return [resource.to_dict() for resource in self.resources.values()]
    
    async def get_resource(self, uri: str) -> Optional[Dict[str, Any]]:
        """Get a specific resource by URI."""
        resource = self.resources.get(uri)
        if resource:
            content = await self._fetch_resource_content(uri)
            return {
                **resource.to_dict(),
                "content": content
            }
        return None
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools."""
        return [tool.to_dict() for tool in self.tools.values()]
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given arguments."""
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found")
        
        self.logger.info(f"Executing tool: {name}")
        try:
            result = await self._execute_tool_implementation(name, arguments)
            self.logger.info(f"Tool {name} executed successfully")
            return {
                "success": True,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Tool {name} execution failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @abstractmethod
    async def _fetch_resource_content(self, uri: str) -> Any:
        """Fetch the actual content of a resource. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def _execute_tool_implementation(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute tool implementation. Must be implemented by subclasses."""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the MCP server."""
        return {
            "status": "healthy",
            "name": self.name,
            "version": self.version,
            "resources_count": len(self.resources),
            "tools_count": len(self.tools),
            "timestamp": datetime.utcnow().isoformat()
        }


class MCPServerManager:
    """
    Manages multiple MCP servers for the educational platform.
    Provides centralized access to all educational data sources.
    """
    
    def __init__(self):
        self.servers: Dict[str, BaseMCPServer] = {}
        self.logger = setup_logging(__name__)
    
    def register_server(self, server: BaseMCPServer) -> None:
        """Register an MCP server."""
        self.servers[server.name] = server
        self.logger.info(f"Registered MCP server: {server.name}")
    
    async def initialize_all(self) -> None:
        """Initialize all registered servers."""
        self.logger.info("Initializing all MCP servers...")
        for server in self.servers.values():
            await server.initialize()
        self.logger.info("All MCP servers initialized")
    
    async def get_all_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get resources from all servers."""
        all_resources = {}
        for name, server in self.servers.items():
            all_resources[name] = await server.list_resources()
        return all_resources
    
    async def get_resource(self, server_name: str, uri: str) -> Optional[Dict[str, Any]]:
        """Get a resource from a specific server."""
        server = self.servers.get(server_name)
        if server:
            return await server.get_resource(uri)
        return None
    
    async def execute_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on a specific server."""
        server = self.servers.get(server_name)
        if not server:
            raise ValueError(f"Server '{server_name}' not found")
        return await server.execute_tool(tool_name, arguments)
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all servers."""
        health_status = {}
        for name, server in self.servers.items():
            health_status[name] = await server.health_check()
        return health_status


# Global MCP server manager instance
mcp_manager = MCPServerManager()
