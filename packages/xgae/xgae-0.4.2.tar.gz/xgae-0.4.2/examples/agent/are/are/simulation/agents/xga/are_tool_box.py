import json
import logging

from typing import Any, Dict, Optional
from typing_extensions import override

from langchain_mcp_adapters.tools import load_mcp_tools

from xgae.engine.engine_base import XGAError, XGAToolSchema, XGAToolResult, XGAToolType
from xgae.engine.mcp_tool_box import XGAMcpToolBox

from are.simulation.tools import Tool
from are.simulation.agents.xga.mcp_tool_executor import convert_mcp_tool_result

class XGAAreToolBox(XGAMcpToolBox):
    def __init__(self, are_tools: Dict[str, Tool]):
        super().__init__()
        self.are_tools = are_tools
        self._is_loaded_are_tool_schemas = False


    @override
    async def init_tool_schemas(self):
        #await self._load_mcp_tools_schema()
        self._load_are_tools_schema()


    @override
    async def call_tool(self, task_id: str, tool_name: str, args: Optional[Dict[str, Any]] = None) -> XGAToolResult:
        task_tool_schemas = self.task_tool_schemas.get(task_id, {})
        tool_schema = task_tool_schemas.get(tool_name, None)
        if tool_schema is None:
            raise XGAError(f"ARE tool not found: '{tool_name}'")
        server_name = tool_schema.server_name

        tool_type = self._get_tool_type(server_name)

        if tool_type == "system":
            tool_args = args or {}
            tool_args = dict({'task_id': task_id}, **tool_args)
            result = self.system_tools.call_tool(tool_name, tool_args)
        elif tool_type == "custom":  # ARE Tools
            try:
                tool_result = self.are_tools[tool_name](**args)
                result = convert_mcp_tool_result(str(tool_result))
            except Exception as e:
                error = f"Call ARE Tool '{tool_name}' error: {str(e)}"
                logging.error(f"AreToolBox call_are_tool: {error}")
                result = XGAToolResult(success=False, output=str(e))
        else:
            raise XGAError(f"ARE tool no support type: '{tool_type}'")

        return result


    async def reload_mcp_tools_schema(self) -> None:
        self._is_loaded_mcp_tool_schemas = False
        self._is_loaded_are_tool_schemas = False
        await self.init_tool_schemas()


    def _load_are_tools_schema(self) -> None:
        if not self._is_loaded_are_tool_schemas:
            for are_tool in self.are_tools.values():
                tool_name = are_tool.name
                server_name , unction_name = tool_name.split("__")
                tool_type :XGAToolType = "custom"
                input_schema = {
                    'properties': are_tool.inputs,
                    'required': []
                }

                tool_schema = XGAToolSchema(tool_name       = tool_name,
                                            function_name   = tool_name,
                                            tool_type       = tool_type,
                                            server_name     = server_name,
                                            description     = are_tool.description,
                                            input_schema    = input_schema,
                                            metadata        = {}
                                            )
                if server_name not in self.mcp_tool_schemas:
                    self.mcp_tool_schemas[server_name] = []
                self.mcp_tool_schemas[server_name].append(tool_schema)
                if server_name not in self.mcp_server_names:
                    self.mcp_server_names.append(server_name)

        self._is_loaded_are_tool_schemas = True