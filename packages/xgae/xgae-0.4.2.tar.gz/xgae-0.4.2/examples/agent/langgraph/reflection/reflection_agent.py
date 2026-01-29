import logging
import os

from typing import Any, Dict, List, Optional, AsyncGenerator
from uuid import uuid4

from langfuse.callback import CallbackHandler
from langfuse import Langfuse

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from langgraph.config import get_stream_writer

from xgae.utils.misc import read_file
from xgae.utils import log_trace

from xgae.engine.engine_base import XGATaskResult
from xgae.engine.mcp_tool_box import XGAMcpToolBox
from xgae.engine.task_engine import XGATaskEngine

from examples.agent.langgraph.reflection.agent_base import AgentContext, TaskState, EvaluateResult
from examples.agent.langgraph.reflection.result_eval_agent import TaskResultEvalAgent
from examples.agent.langgraph.reflection.custom_prompt_rag import CustomPromptRag


class ReflectiontAgent:
    MAX_TASK_RETRY = 2
    QUALIFIED_RESULT_SCORE = 0.7

    def __init__(self, use_prompt_rag: Optional[bool] = False):
        self.graph = None

        self.graph_config = None
        self.graph_langfuse = None
        self.task_engine: XGATaskEngine = None

        self.tool_box = XGAMcpToolBox(custom_mcp_server_file="xga_mcp_servers.json")
        self.result_eval_agent = TaskResultEvalAgent()

        if use_prompt_rag:
            self.custom_prompt_rag = CustomPromptRag()

    async def _create_graph(self) -> StateGraph:
        try:
            graph_builder = StateGraph(TaskState)

            # Add nodes
            graph_builder.add_node('supervisor', self._supervisor_node)
            graph_builder.add_node('prompt_optimize', self._prompt_optimize_node)
            graph_builder.add_node('select_tool', self._select_tool_node)
            graph_builder.add_node('exec_task', self._exec_task_node)
            graph_builder.add_node('final_result', self._final_result_node)

            # Add edges
            graph_builder.add_edge(START, 'supervisor')
            graph_builder.add_conditional_edges(
                'supervisor',
                self._next_condition,
                {
                    'select_tool'       : 'select_tool',
                    'exec_task'         : 'exec_task',
                    'prompt_optimize'   : 'prompt_optimize',
                    'end'               : END
                }
            )

            graph_builder.add_edge('prompt_optimize', 'select_tool')
            graph_builder.add_edge('select_tool', 'exec_task')
            graph_builder.add_edge('exec_task', 'final_result')

            graph_builder.add_conditional_edges(
                'final_result',
                self._next_condition,
                {
                    'supervisor': 'supervisor',
                    'exec_task' : 'exec_task',
                    'end'       : END
                }
            )
            
            graph = graph_builder.compile(checkpointer=MemorySaver())
            graph.name = "XGARectAgentGraph"

            return graph
        except Exception as e:
            logging.error("Failed to create XGARectAgent Graph: %s", str(e))
            raise


    def _search_system_prompt(self, user_input: str) -> str:
        system_prompt = None
        if hasattr(self, 'custom_prompt_rag'):
            system_prompt_path = self.custom_prompt_rag.search_prompt(user_input)
            if system_prompt_path:
                system_prompt = read_file(system_prompt_path)
        else:
            if "fault" in user_input:  # only for example
                system_prompt = read_file("templates/example/fault_user_prompt.md")
        return system_prompt


    async def _supervisor_node(self, state: TaskState) -> Dict[str, Any]:
        user_input = state['user_inputs'][0]
        eval_result = state.get('eval_result', None)
        system_prompt = state.get('system_prompt', None)

        if system_prompt is  None and eval_result is None:
            system_prompt = self._search_system_prompt(user_input)
        is_system_prompt = True if system_prompt is not None else False

        general_tools = [] if system_prompt else ["*"]
        custom_tools = ["*"] if system_prompt  else []

        task_plan_score = None
        if eval_result and 'task_plan' in eval_result and 'score' in eval_result['task_plan']:
            task_plan_score = eval_result['task_plan'].get('score', 1.0)

        function_call_score = None
        if eval_result and 'function_call' in eval_result and 'score' in eval_result['function_call']:
            function_call_score = eval_result['function_call'].get('score', 1.0)

        super_state = {}
        if task_plan_score and task_plan_score < self.QUALIFIED_RESULT_SCORE:
            next_node = "prompt_optimize"
            super_state = self._prepare_task_retry(state)
            logging.warning(f"****** ReactAgent TASK_RETRY: task_plan_score={task_plan_score} < {self.QUALIFIED_RESULT_SCORE} , "
                            f"Start Optimize Prompt ...")
        elif function_call_score and function_call_score < self.QUALIFIED_RESULT_SCORE:
            next_node = "select_tool"
            super_state = self._prepare_task_retry(state)
            logging.warning(f"****** ReactAgent TASK_RETRY: function_call_score={function_call_score} < {self.QUALIFIED_RESULT_SCORE} , "
                            f"Select Tool Again ...")
        elif eval_result is not None:  # retry condition is not satisfied, end task
            next_node = "end"
        else:
            next_node = "select_tool" if is_system_prompt else "exec_task"

        logging.info(f"ReactAgent supervisor_node: is_system_prompt={is_system_prompt}, next_node={next_node}")

        super_state['next_node']        = next_node
        super_state['system_prompt']    = system_prompt
        super_state['custom_tools']     = custom_tools
        super_state['general_tools']    = general_tools

        return super_state


    async def _prompt_optimize_node(self, state: TaskState) -> Dict[str, Any]:
        system_prompt = state['system_prompt']
        logging.info("ReactAgent prompt_optimize_node: optimize system prompt")
        # @todo optimize system prompt in future
        return {
            'system_prompt' : system_prompt,
        }


    def _select_custom_tools(self, system_prompt: str) -> list[str]:
        # @todo search mcp tool based on system prompt or user_input in future
        custom_tools = ["*"] if system_prompt  else []
        return custom_tools


    async def _select_tool_node(self, state: TaskState) -> Dict[str, Any]:
        system_prompt = state.get('system_prompt',None)
        general_tools = []

        logging.info("ReactAgent select_tool_node: select tool based on system_prompt")
        custom_tools = self._select_custom_tools(system_prompt)
        return {
            'general_tools' : general_tools,
            'custom_tools'  : custom_tools,
        }


    async def _exec_task_node(self, state: TaskState) -> Dict[str, Any]:
        user_input = state['user_inputs'][0]
        system_prompt = state.get('system_prompt',None)
        general_tools = state.get('general_tools',[])
        custom_tools = state.get('custom_tools',[])
        retry_count = state.get('retry_count', 0)
        task_no = state.get('task_no', 0)
        is_system_prompt = True if system_prompt is not None else False

        trace_id = self.graph_langfuse.get_trace_id()
        llm_messages = []
        try:
            logging.info(f"🔥 ReactAgent exec_task_node: user_input={user_input}, general_tools={general_tools}, "
                         f"custom_tools={custom_tools}, is_system_prompt={is_system_prompt}")

            # if langgraph resume , must use same task engine
            if self.task_engine is None:
                self.task_engine = XGATaskEngine(
                    task_id         = state['agent_context']['task_id'],
                    task_no         = task_no,
                    session_id      = state['agent_context'].get('session_id', None),
                    user_id         = state['agent_context'].get('user_id', None),
                    agent_id        = state['agent_context'].get('agent_id', None),
                    tool_box        = self.tool_box,
                    general_tools   = general_tools,
                    custom_tools    = custom_tools,
                    system_prompt   = system_prompt
                )
                retry_count += 1

            chunks = []
            stream_writer = get_stream_writer()
            async for chunk in self.task_engine.run_task(task_input={"role": "user", "content": user_input},
                                                         trace_id=trace_id):
                chunks.append(chunk)
                stream_writer({"engine_message": chunk})

            task_result = self.task_engine.parse_final_result(chunks)
            llm_messages = self.task_engine.get_history_llm_messages()
            task_no += 1  # a task use unique task_no, no matter retry n times
        except Exception as e:
            logging.error(f"XReactAgent exec_task_node: Failed to execute task: {e}")
            task_result = XGATaskResult(type="error", content="Failed to execute task")

        return {
            'task_result'   : task_result,
            'retry_count'   : retry_count,
            'llm_messages'  : llm_messages.copy(),
            'task_no'       : task_no,
        }


    async def _final_result_node(self, state: TaskState) -> Dict[str, Any]:
        user_inputs = state['user_inputs']
        task_result = state['task_result']
        llm_messages = state['llm_messages']
        agent_context = state['agent_context']
        system_prompt = state.get('system_prompt', None)
        retry_count = state['retry_count']

        is_system_prompt = True if system_prompt is not None else False

        next_node = "end"
        final_result = task_result
        eval_result = None
        if task_result['type'] == "ask":
            logging.info(f"XReactAgent final_result_node: ASK_USER_QUESTION: {task_result['content']}")
            ask_input = interrupt({
                'final_result' : task_result
            })
            logging.info(f"XReactAgent final_result_node: ASK_USER_ANSWER: {ask_input}")
            next_node = "exec_task"
            user_inputs.insert(0, ask_input)
            final_result = None
        elif is_system_prompt and retry_count < self.MAX_TASK_RETRY:
            trace_id = self.graph_langfuse.get_trace_id()
            session_id = agent_context.get('session_id', None)
            task_input = ", ".join(reversed(user_inputs))
            eval_result = await self.result_eval_agent.eval_result(task_input, system_prompt, task_result,
                                                                   llm_messages, trace_id, session_id)
            if 'task_result' in eval_result and 'score' in eval_result['task_result']:
                score =  eval_result['task_result'].get('score', 1.0)
                if score < self.QUALIFIED_RESULT_SCORE:
                    next_node = "supervisor"
        
        logging.info(f"ReactAgent final_result_node: next_node={next_node}")
        
        return {
            'user_inputs'    : user_inputs,
            'next_node'     : next_node,
            'final_result'  : final_result,
            'eval_result'   : eval_result
        }


    def _next_condition(self, state: TaskState) -> str:
        next_node = state['next_node']
        return next_node


    async def generate_with_result(self, user_input: str,
                                   agent_context: Optional[AgentContext] = None,
                                   is_resume: Optional[bool]=False) -> XGATaskResult:
        agent_context = agent_context or {}
        try:

            if is_resume:
                logging.info(f"=== Start React Agent for USER_ASK_ANSWER: {user_input}")
                graph_input = Command(resume=user_input)
            else:
                logging.info(f"=== Start React Agent for USER_INPUT: {user_input}")
                graph_input = await self._prepare_graph_start(user_input, agent_context)

            final_state = await self.graph.ainvoke(graph_input, config=self.graph_config)

            if "__interrupt__" in final_state:
                interrupt_event = final_state["__interrupt__"][0]
                interrupt_value = interrupt_event.value
                result = interrupt_value['final_result']
            else:
                result = final_state['final_result']

            return result
        except Exception as e:
            log_trace(e, f"XReactAgent generate: user_input={user_input}")
            result = XGATaskResult(type="error", content=f"React Agent error: {e}")
            return result


    async def generate(self, user_input: str,
                       agent_context: Optional[AgentContext]=None,
                       is_resume: Optional[bool]=False) -> AsyncGenerator[Dict[str, Any], None]:
        agent_context = agent_context or {}
        try:
            if is_resume:
                logging.info(f"=== Start React Stream Agent for USER_ASK_ANSWER: {user_input}")
                graph_input = Command(resume=user_input)
            else:
                logging.info(f"=== Start React Stream Agent USER_ASK_ANSWER: {user_input}")
                graph_input = await self._prepare_graph_start(user_input, agent_context)

            async for msg_type, message in self.graph.astream(input=graph_input,
                                                              config=self.graph_config,
                                                              stream_mode=["custom", "updates"]):
                if msg_type == "updates" and '__interrupt__' in message:
                    interrupt_event = message["__interrupt__"][0]
                    interrupt_value = interrupt_event.value
                    final_result = interrupt_value['final_result']
                    yield final_result
                elif msg_type == "updates" and 'final_result' in message:
                    message = message['final_result']
                    final_result = message.get('final_result', None)
                    if final_result:
                        yield final_result
                elif msg_type == "custom" and 'engine_message' in message:
                    message = {'type': "message", 'content': message['engine_message']}
                    yield message

        except Exception as e:
            log_trace(e, f"XReactAgent generate: user_input={user_input}")
            yield {'type': "error", 'content': f"React Agent generate error: {e}"}


    async def _prepare_graph_start(self, user_input, agent_context: AgentContext)->TaskState:
        if self.graph is None:
            self.graph = await self._create_graph()

        self._clear_graph()

        agent_context = agent_context or {}
        task_id = agent_context.get("task_id", f"xga_task_{uuid4()}")
        agent_context["task_id"] = task_id
        thread_id = agent_context.get('thread_id', task_id)
        agent_context['thread_id'] = thread_id
        session_id = agent_context.get('session_id', task_id)
        agent_context['session_id'] = session_id


        langfuse_handler = self._get_langfuse_handler(agent_context)
        callbacks = None
        if langfuse_handler:
            callbacks = [langfuse_handler]
            self.graph_langfuse = langfuse_handler.langfuse
        else:
            self.graph_langfuse = Langfuse(enabled=False)

        self.graph_config = {
            'recursion_limit': 100,
            'configurable': {
                'thread_id': thread_id
            },
            'callbacks': callbacks
        }

        graph_input = {
            'user_inputs'       : [user_input],
            'next_node'         : None,
            'agent_context'     : agent_context,
            'retry_count'       : 0,
            'task_no'           : 0
        }

        return graph_input


    def _get_langfuse_handler(self, agent_context: AgentContext)->CallbackHandler:
        langfuse_handler = None
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

        if public_key and secret_key:
            langfuse_handler =  CallbackHandler(
                public_key  = public_key,
                secret_key  = secret_key,
                host        = host,
                trace_name  = "xga_react_agent",
                session_id  = agent_context.get('session_id', None),
                user_id     = agent_context.get('user_id', None),
            )
        return langfuse_handler


    def _clear_graph(self):
        self.graph_config = None
        self.graph_langfuse = None
        self.task_engine: XGATaskEngine = None


    def _prepare_task_retry(self, state: TaskState)-> Dict[str, Any]:
        self.task_engine = None
        user_inputs = state['user_inputs']
        task_input = ", ".join(reversed(user_inputs))

        return {
            'user_inputs'   : [task_input],
            'llm_messages'  : [],
            'task_result'   : None,
            'final_result'  : None,
            'eval_result'   : None,
        }