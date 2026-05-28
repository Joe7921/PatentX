import sys
import os
import asyncio
from typing import Dict, Any, List
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClientManager:
    """
    单例模式管理 MCP Client 的生命周期。
    自动启动 mcp_server.py 子进程并提供 OpenAI-compatible 的 Schema。
    """
    _instance = None
    
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        server_script = os.path.join(current_dir, "mcp_server.py")
        
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=[server_script],
            env=os.environ.copy()
        )
        self.session = None
        self._exit_stack = None
        self._tools_cache = None

    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance.connect()
        return cls._instance

    async def connect(self):
        self._exit_stack = AsyncExitStack()
        
        # Connect to stdio server
        transport = await self._exit_stack.enter_async_context(stdio_client(self.server_params))
        self.read, self.write = transport
        
        self.session = await self._exit_stack.enter_async_context(ClientSession(self.read, self.write))
        await self.session.initialize()
        
    async def get_tools_schema(self) -> List[Dict[str, Any]]:
        """将 MCP 的工具列表转换为 OpenAI function calling 所需的 Schema 格式"""
        if self._tools_cache is not None:
            return self._tools_cache
            
        tools_resp = await self.session.list_tools()
        schemas = []
        for tool in tools_resp.tools:
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            })
        self._tools_cache = schemas
        return schemas

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """执行 MCP 工具调用并返回文本结果"""
        try:
            result = await self.session.call_tool(name, arguments)
            if result.isError:
                return f"Tool Execution Error: {result.content}"
            
            texts = [c.text for c in result.content if c.type == "text"]
            return "\n".join(texts)
        except Exception as e:
            return f"System Error calling tool {name}: {str(e)}"

    async def cleanup(self):
        """关闭子进程与连接"""
        if self._exit_stack:
            await self._exit_stack.aclose()
            self._exit_stack = None
            MCPClientManager._instance = None
