"""Kubernetes MCP server integration."""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import threading
from typing import List, Optional
import logging

try:
    from mcp import ClientSession, stdio_client, StdioServerParameters

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    ClientSession = None  # type: ignore
    stdio_client = None  # type: ignore
    StdioServerParameters = None  # type: ignore

logger = logging.getLogger(__name__)


class KubernetesMCPServer:
    """Wrapper for the official Kubernetes MCP server."""

    def __init__(self, timeout: int = 300):
        self.timeout = timeout
        self.session: Optional[ClientSession] = None
        self._client_cm = None
        self._server_params_chain: List[StdioServerParameters] = []
        if MCP_AVAILABLE:
            kubeconfig = os.getenv("KUBECONFIG", os.path.expanduser("~/.kube/config"))
            self._server_params_chain = [
                StdioServerParameters(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-kubernetes"],
                    env={"KUBECONFIG": kubeconfig},
                ),
                StdioServerParameters(
                    command="uvx",
                    args=["--from", "mcp-server-kubernetes", "mcp-server-kubernetes"],
                    env={"KUBECONFIG": kubeconfig},
                ),
            ]

    async def connect(self) -> Optional[ClientSession]:
        if not MCP_AVAILABLE:
            logger.warning("MCP python client is not installed. Install `mcp` to enable MCP features.")
            return None

        if self.session:
            return self.session

        last_error: Optional[Exception] = None
        for params in self._server_params_chain:
            try:
                self._client_cm = stdio_client(params)
                read_stream, write_stream = await self._client_cm.__aenter__()
                self.session = ClientSession(read_stream, write_stream)
                await self.session.initialize()
                logger.info("Connected to Kubernetes MCP server via %s", params.command)
                return self.session
            except Exception as exc:  # pragma: no cover - best effort connection
                last_error = exc
                logger.warning("Failed to start MCP server via %s: %s", params.command, exc)
        if last_error:
            raise last_error
        return None

    async def disconnect(self):
        self.session = None
        if self._client_cm:
            try:
                await self._client_cm.__aexit__(None, None, None)
            except Exception as exc:  # pragma: no cover
                logger.warning("Error closing MCP stdio client: %s", exc)
            self._client_cm = None

    async def list_tools(self) -> List:
        session = await self.connect()
        if not session:
            return []
        try:
            result = await session.list_tools()
            return result.tools or []
        except Exception as exc:
            logger.error("Error listing MCP tools: %s", exc)
            return []

    async def call_tool(self, name: str, arguments: Optional[dict] = None) -> str:
        session = await self.connect()
        if not session:
            raise RuntimeError("MCP server not available")

        result = await session.call_tool(name, arguments or {})
        if result.isError:
            raise RuntimeError(result.error.message if result.error else f"Tool {name} failed.")

        output_parts: List[str] = []
        if result.content:
            for item in result.content:
                text = getattr(item, "text", None)
                if text:
                    output_parts.append(text)
        if result.structuredContent:
            output_parts.append(json.dumps(result.structuredContent, indent=2))
        if result.text:
            output_parts.append(result.text)
        output = "\n".join(part for part in output_parts if part).strip()
        return output or "Command executed successfully (no output)."

    async def run_kubectl(self, command: str) -> str:
        try:
            return await self.call_tool("kubectl", {"command": command})
        except Exception as exc:
            logger.warning("MCP kubectl command failed: %s. Falling back to local kubectl.", exc)
            return self._run_local_kubectl(command, error=str(exc))

    def run_kubectl_sync(self, command: str) -> str:
        try:
            return asyncio.run(self.run_kubectl(command))
        except RuntimeError as exc:
            if "asyncio.run()" not in str(exc):
                raise

            result_holder: dict[str, str] = {}
            error_holder: dict[str, Exception] = {}

            def runner():
                try:
                    result_holder["value"] = asyncio.run(self.run_kubectl(command))
                except Exception as run_exc:  # pragma: no cover
                    error_holder["error"] = run_exc

            thread = threading.Thread(target=runner, daemon=True)
            thread.start()
            thread.join()

            if "error" in error_holder:
                raise error_holder["error"]
            return result_holder.get("value", "Command executed (no output returned).")

    def _run_local_kubectl(self, command: str, error: Optional[str] = None) -> str:
        full_command = command if command.strip().startswith("kubectl") else f"kubectl {command}"
        try:
            completed = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                shell=True,
                timeout=self.timeout,
            )
        except Exception as exc:  # pragma: no cover
            return f"Failed to execute '{full_command}': {exc}"

        output = completed.stdout.strip()
        if completed.returncode != 0:
            fallback_msg = completed.stderr.strip() or "Unknown kubectl error."
            if error:
                fallback_msg = f"{fallback_msg}\n(MCP error: {error})"
            return f"kubectl command failed:\n{fallback_msg}"
        if error:
            output = f"{output}\n\n(MCP fallback triggered: {error})"
        return output or "kubectl command completed (no output)."

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

