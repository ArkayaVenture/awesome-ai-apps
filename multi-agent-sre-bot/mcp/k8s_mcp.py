"""Kubernetes MCP server integration."""
import os
import asyncio
from typing import Optional, List
import logging

# Try to import MCP, but make it optional
# Note: agents package requires tensorflow which may not be available for Python 3.13+
MCP_AVAILABLE = False
MCPServer = None
MCPServerStdio = None

try:
    from agents.mcp import MCPServer, MCPServerStdio
    MCP_AVAILABLE = True
except ImportError:
    # MCP not available - this is OK, the bot will work without it
    pass

logger = logging.getLogger(__name__)


class KubernetesMCPServer:
    """Wrapper for Kubernetes MCP server."""
    
    def __init__(self, timeout: int = 300):
        """Initialize Kubernetes MCP server.
        
        Args:
            timeout: Timeout in seconds for MCP operations
        """
        self.timeout = timeout
        self.server: Optional[object] = None  # MCPServer if MCP_AVAILABLE
    
    async def connect(self) -> Optional[MCPServer]:
        """Connect to Kubernetes MCP server.
        
        Returns:
            MCPServer instance or None if MCP is not available
        """
        if not MCP_AVAILABLE:
            logger.warning("MCP not available. MCP features will be disabled.")
            return None
        
        try:
            # Use official Kubernetes MCP server
            # This assumes the MCP server is available via npx
            self.server = MCPServerStdio(
                cache_tools_list=True,
                params={
                    "command": "npx",
                    "args": [
                        "-y",
                        "@modelcontextprotocol/server-kubernetes"
                    ],
                    "env": {
                        "KUBECONFIG": os.getenv("KUBECONFIG", "~/.kube/config"),
                    }
                },
            )
            
            await self.server.__aenter__()
            logger.info("Connected to Kubernetes MCP server")
            return self.server
            
        except Exception as e:
            logger.error(f"Failed to connect to Kubernetes MCP server: {e}")
            # Fallback: try alternative MCP server path
            try:
                self.server = MCPServerStdio(
                    cache_tools_list=True,
                    params={
                        "command": "uvx",
                        "args": [
                            "--from",
                            "mcp-server-kubernetes",
                            "mcp-server-kubernetes"
                        ],
                        "env": {
                            "KUBECONFIG": os.getenv("KUBECONFIG", "~/.kube/config"),
                        }
                    },
                )
                await self.server.__aenter__()
                logger.info("Connected to Kubernetes MCP server (fallback)")
                return self.server
            except Exception as e2:
                logger.error(f"Failed to connect with fallback: {e2}")
                raise
    
    async def disconnect(self):
        """Disconnect from MCP server."""
        if self.server:
            try:
                await self.server.__aexit__(None, None, None)
                logger.info("Disconnected from Kubernetes MCP server")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
    
    async def list_tools(self) -> List:
        """List available tools from MCP server.
        
        Returns:
            List of available tools
        """
        if not MCP_AVAILABLE:
            return []
        
        if not self.server:
            await self.connect()
        
        if not self.server:
            return []
        
        try:
            tools = await self.server.list_tools()
            return tools
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return []
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

