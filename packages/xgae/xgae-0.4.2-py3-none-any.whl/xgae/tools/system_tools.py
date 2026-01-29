import logging

from typing import List, Optional, Dict, Any

from xgae.engine.engine_base import XGAError, XGAToolSchema, XGAToolBox, XGAToolResult, XGAToolType

class XGASystemTools:
    SYSTEM_SERVER_NAME = "XgaSystem"

    def get_sys_tool_schemas(self) -> List[XGAToolSchema] :
        sys_tool_schemas = []
        sys_tool_schemas.append(self._get_complete_tool_schema())
        sys_tool_schemas.append(self._get_ask_tool_schema())
        return sys_tool_schemas


    def call_tool(self, tool_name: str, args: Optional[Dict[str, Any]] = None) -> XGAToolResult:
        args = args or {}
        try:
            method = getattr(self, tool_name)
        except AttributeError:
            raise ValueError(f"XGASystemTools call_tool: System Tool function '{tool_name}' not found.")

        if not callable(method):
            raise ValueError(f"XGASystemTools call_tool: '{tool_name}' is not a callable function.")

        return method(**args)


    def complete(self, task_id: str, text: str=None, attachments: str=None)->XGAToolResult :
        logging.info(f"<XGAETools-complete>: task_id={task_id}, text={text}, attachments={attachments}")
        return XGAToolResult(success=True, output=str({"status": "complete"}))


    def ask(self, task_id: str, text: str=None, attachments: str=None)->XGAToolResult :
        logging.info(f"<XGAETools-ask>: task_id={task_id}, text={text}, attachments={attachments}")
        return XGAToolResult(success=True, output=str({"status": "Awaiting user response..."}))


    def _get_complete_tool_schema(self)->XGAToolSchema :
        return XGAToolSchema(
            tool_name       = "complete",
            function_name   = "complete",
            tool_type       = "system",
            server_name     = self.SYSTEM_SERVER_NAME,
            description     = """A special tool to indicate you have completed all tasks and are about to enter complete state. Use ONLY when: 1) All tasks in todo.md are marked complete [x], 2) The user's original request has been fully addressed, 3) There are no pending actions or follow-ups required, 4) You've delivered all final outputs and results to the user. IMPORTANT: This is the ONLY way to properly terminate execution. Never use this tool unless ALL tasks are complete and verified. Always ensure you've provided all necessary outputs and references before using this tool. Include relevant attachments when the completion relates to specific files or resources.""",
            input_schema    = {
                'type': 'object',
                'required': ['text'],
                'properties': {
                    'text': {
                        'type': 'string',
                        'default': None,
                        'description': 'Completion summary. Include: 1) Task summary 2) Key deliverables 3) Next steps 4) Impact achieved'
                    },
                    'attachments': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'default': None,
                        'description': 'Comma-separated list of final outputs. Use when: 1) Completion relates to files 2) User needs to review outputs 3) Deliverables in files'
                    }
                }
            },
            metadata        = None
        )


    def _get_ask_tool_schema(self)->XGAToolSchema :
        return XGAToolSchema(
            tool_name       = "ask",
            function_name   = "ask",
            tool_type       = "system",
            server_name     = self.SYSTEM_SERVER_NAME,
            description     = """Ask user a question and wait for response. Use for: 1) Requesting clarification on ambiguous requirements, 2) Seeking confirmation before proceeding with high-impact changes, 3) Gathering additional information needed to complete a task, 4) Offering options and requesting user preference, 5) Validating assumptions when critical to task success, 6) When encountering unclear or ambiguous results during task execution, 7) When tool results don't match expectations, 8) For natural conversation and follow-up questions, 9) When research reveals multiple entities with the same name, 10) When user requirements are unclear or could be interpreted differently. IMPORTANT: Use this tool when user input is essential to proceed. Always provide clear context and options when applicable. Use natural, conversational language that feels like talking with a helpful friend. Include relevant attachments when the question relates to specific files or resources. CRITICAL: When you discover ambiguity (like multiple people with the same name), immediately stop and ask for clarification rather than making assumptions.""",
            input_schema    = {
                'type': 'object',
                'required': ['text'],
                'properties': {
                    'text': {
                        'type': 'string',
                        'default': None,
                        'description': 'Question text to present to user. Include: 1) Clear question/request 2) Context why input is needed 3) Available options 4) Impact of choices 5) Relevant constraints'
                    },
                    'attachments': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'default': None,
                        'description': 'Comma-separated list of files/URLs to attach. Use when: 1) Question relates to files/configs 2) User needs to review content 3) Options documented in files 4) Supporting evidence needed'
                    }
                }
            },
            metadata        = None
        )


if __name__ == "__main__":
    from xgae.utils.setup_env import setup_logging
    setup_logging()

    system_tools = XGASystemTools()

    tool_name = "complete"
    args = {
        'task_id': "task1",
        'text': "complete task",
        'attachments': 'complete attachments'
    }
    result = system_tools.call_tool(tool_name, args)
    print(result)

    tool_name = "ask"
    args = {
        'task_id': "task2",
        'text': "ask task",
        'attachments': 'ask attachments'
    }
    result = system_tools.call_tool(tool_name, args)
    print(result)