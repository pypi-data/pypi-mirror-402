from typing import Any, Dict, List, TypedDict, Optional

from xgae.engine.engine_base import XGATaskResult

class EvaluateResult(TypedDict, total=False):
    task_result: Dict[str, Any]
    task_process: Dict[str, Any]
    function_call: Dict[str, Any]

class AgentContext(TypedDict, total=False):
    task_id: str
    session_id: str
    user_id: str
    agent_id: str
    thread_id: str


class TaskState(TypedDict, total=False):
    """State definition for the agent orchestration graph"""
    llm_messages: List[Dict[str, Any]]
    user_inputs: List[str]
    next_node: str
    system_prompt: str
    custom_tools: List[str]
    general_tools: List[str]
    task_result: XGATaskResult
    final_result: XGATaskResult
    eval_result: EvaluateResult
    retry_count: int
    task_no: int
    agent_context: AgentContext


