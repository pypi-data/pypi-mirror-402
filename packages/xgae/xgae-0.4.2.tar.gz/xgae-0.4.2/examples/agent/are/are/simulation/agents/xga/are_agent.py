import re
import asyncio
from typing import List, Dict, Any

from mammoth.results import success
from typing_extensions import override

from are.simulation.agents.are_simulation_agent import AgentStoppedException
from are.simulation.agents.llm.types import MMObservation
from are.simulation.agents.multimodal import Attachment, attachments_to_pil
from are.simulation.agents.agent_log import (
    LLMInputLog,
    LLMOutputThoughtActionLog,
    StepLog,
    StopLog,
    SystemPromptLog,
    ThoughtLog,
    ToolCallLog,
    FinalAnswerLog,
    ObservationLog,
    ErrorLog
)
from are.simulation.agents.default_agent.base_agent import (
    BaseAgent,
    RunningState,
    get_offset_from_time_config_mode
)

from xgae.utils.llm_client import LLMConfig
from xgae.gaia2.are_engine import ARETaskEngine
from are.simulation.agents.xga.are_tool_box import XGAAreToolBox
from are.simulation.agents.xga.are_prompt_builder import XGAArePromptBuilder

def pre_run_task_check(agent, iterations: int, llm_messages: List[Dict[str, Any]]):
    try:
        agent.logger.info(f"\n\n------  Starting Run Task Iteration {iterations}...   ------")

        if iterations == 0:
            agent.system_prompt = agent.task_engine.task_prompt
            agent.logger.info(f"------  SYSTEM_PROMPT   ------ \n{agent.system_prompt}\n")
            agent.append_agent_log(
                SystemPromptLog(
                    content     = agent.system_prompt,
                    timestamp   = agent.make_timestamp(),
                    agent_id    = agent.agent_id,
                )
            )

        agent.append_agent_log(
            StepLog(
                iteration   = agent.iterations,
                timestamp   = agent.make_timestamp(),
                agent_id    = agent.agent_id,
            )
        )

        if agent.stop_event.is_set():
            agent.logger.info(f"pre_run_task_check[{iterations}]: Recv Stop Event before condition, raise AgentStoppedException")
            raise AgentStoppedException("Agent stopped.")

        # Execute a pre_step() function if it exists
        for conditional_step in agent.conditional_pre_steps:
            if conditional_step.condition is None or conditional_step.condition(agent):
                conditional_step.function(agent)

        if agent.stop_event.is_set():
            agent.logger.info(f"pre_run_task_check[{iterations}]: Recv Stop Event after condition, raise AgentStoppedException")
            raise AgentStoppedException("Agent stopped.")

        # Begin step()
        agent.build_history_from_logs(
            exclude_log_types=["tool_call", "rationale", "action"]
        )

        agent.append_agent_log(
            LLMInputLog(
                content     = llm_messages,
                timestamp   = agent.make_timestamp(),
                agent_id    = agent.agent_id
            )
        )

        if agent.simulated_generation_time_config is not None:
            if agent.pause_env is None:
                raise ValueError("pause_env is not set")
            agent.pause_env()
    except Exception as e:
        agent.log_error(e)
        agent.logger.info(f"pre_run_task_check[{iterations}]: Exception Occur, Stop task")
        agent.task_engine.stop_task()


def post_run_task_check(agent, iterations: int, llm_response: Dict[str, Any]):
    try:
        agent.logger.info(f"------  LLM Response Iteration [{iterations}]   ------ \n{llm_response}\n")

        llm_output = str(llm_response)

        # Resume the environment after the generation of a thought/action if needed
        if agent.simulated_generation_time_config is not None:
            if agent.resume_env is None:
                raise ValueError("resume_env is not set")

            offset = get_offset_from_time_config_mode(
                time_config = agent.simulated_generation_time_config,
                completion_duration = 0,
            )
            agent.logger.info(f"post_run_task_check[{iterations}]: Resuming environment with {offset} offset")
            agent.resume_env(offset)

        metadata = {}
        agent.append_agent_log(
            LLMOutputThoughtActionLog(
                content             = llm_output,
                timestamp           = agent.make_timestamp(),
                agent_id            = agent.agent_id,
                prompt_tokens       = metadata.get("prompt_tokens", 0),
                completion_tokens   = metadata.get("completion_tokens", 0),
                total_tokens        = metadata.get("total_tokens", 0),
                reasoning_tokens    = metadata.get("reasoning_tokens", 0),
                completion_duration = metadata.get("completion_duration", 0),
            )
        )
        # end step()

        if agent.stop_event.is_set():
            agent.logger.info(f"post_run_task_check[{iterations}]: Recv Stop Event, raise AgentStoppedException")
            raise AgentStoppedException("Agent stopped.")

        # Execute a post_step() function if it exists (polling the Meta Agents Research Environments notifications for example)
        for conditional_step in agent.conditional_post_steps:
            if conditional_step.condition is None or conditional_step.condition(agent):
                conditional_step.function(agent)
    except Exception as e:
        agent.log_error(e)
        agent.logger.info(f"post_run_task_check[{iterations}]: Exception Occur, Stop task")
        agent.task_engine.stop_task()
    finally:
        if agent.simulated_generation_time_config and agent.resume_env:
            agent.resume_env(0.0)  # Resume without advancing time

        agent.iterations += 1
        agent.planning_counter += 1


def terminate_task_check(agent, iterations: int) -> bool:
    is_terminate_task = False

    try:
        if agent.termination_step and agent.termination_step.condition:
            is_terminate_task = agent.termination_step.condition(agent)
            if is_terminate_task:
                agent.logger.info(f"terminate_task_check[{iterations}]: termination_step.condition is True")
    except Exception as e:
        agent.log_error(e)

    return is_terminate_task


class XGAAreAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.task_engine: ARETaskEngine = None


    @override
    def initialize(self, attachments: list[Attachment] | None = None, **kwargs) -> None:
        self.logs = []
        self.iterations = 0
        self.planning_counter = 0

        tool_box = XGAAreToolBox(self.tools)

        general_system_prompt = "\n\n".join(prompt for prompt in self.init_system_prompts.values())
        prompt_builder = XGAArePromptBuilder(general_system_prompt)

        model_config = self.llm_engine.model_config
        llm_config = LLMConfig(
            model       = model_config.model_name,
            api_key     = model_config.api_key,
            api_base    = model_config.endpoint
        )

        self.task_engine =  ARETaskEngine(
            agent               = self,
            agent_id            = self.agent_id,
            max_auto_run        = self.max_iterations,
            llm_config          = llm_config,
            tool_box            = tool_box,
            prompt_builder      = prompt_builder,
            pre_run_task_fn     = pre_run_task_check,
            post_run_task_fn    = post_run_task_check,
            terminate_task_fn   = terminate_task_check,
        )

        # Reload the agent state if logs are provided
        start_logs = kwargs.pop("start_logs", [])
        if start_logs:
            self.replay(start_logs)

        # Include additional image PILs directly into state stack.
        if attachments:
            images = attachments_to_pil(attachments)
            self.action_executor.inject_state({f"image_{i}": image for i, image in enumerate(images)})
            self.logger.debug(f"XGAAreAgent initialize: Injecting images into states for {len(images)} images")
            self.logger.debug(f"XGAAreAgent initialize: New Keys {','.join(self.action_executor.state.keys())}")

        self.initialized = True


    @override
    def execute_agent_loop(self) -> str | None | MMObservation:
        with asyncio.Runner() as runner:
            runner.run(self.async_execute_agent_loop())

        # We have reached a termination condition, execute the termination method
        if self.termination_step.function is not None and not self.stop_event.is_set():
            return self.termination_step.function(self)


    async def async_execute_agent_loop(self) -> str | None | MMObservation:
        chunks = []
        async for chunk in self.task_engine.run_task(task_input={"role": "user", "content": self.task}):
            chunks.append(chunk)
            chunk_type = chunk['type']
            if chunk_type== "status":
                status_content = chunk['content']
                status_type = status_content['status_type']
                if status_type == "error":
                    error_msg = chunk.get('message')
                    self.logger.warning(f"XGAAreAgent execute_agent_loop: Fatal error - {error_msg}")
                    self.log_error(error_msg)
                elif status_type == "stop":
                    error_msg = chunk.get('message')
                    self.logger.warning("XGAAreAgent execute_agent_loop: Agent stopped.")
                    self.append_agent_log(
                        StopLog(
                            content     = f"Agent stopped - {error_msg}",
                            timestamp   = self.make_timestamp(),
                            agent_id    = self.agent_id,
                        )
                    )
            elif chunk_type == "assistant":
                llm_content  = chunk['content']['content']
                if "<thought>" in llm_content:
                    thought_content = re.search(r'<thought>(.*?)</thought>', llm_content, re.DOTALL).group(1).strip()
                    if thought_content:
                        self.append_agent_log(
                            ThoughtLog(
                                content     = thought_content,
                                timestamp   = self.make_timestamp(),
                                agent_id    = self.agent_id,
                            )
                        )
            elif chunk_type == "tool":
                tool_content = chunk['content']
                tool_execution = tool_content.get('tool_execution')
                tool_result = tool_execution.get('result')
                self.append_agent_log(
                    ObservationLog(
                        content     = str(tool_result),
                        attachments = [],
                        timestamp   = self.make_timestamp(),
                        agent_id    = self.agent_id,
                    )
                )

                self.append_agent_log(
                    ToolCallLog(
                        tool_name       = tool_execution.get('function_name'),
                        tool_arguments  = tool_execution.get('arguments'),
                        timestamp       = self.make_timestamp(),
                        agent_id        = self.agent_id,
                    )
                )
            #print(chunk)

        final_result = self.task_engine.parse_final_result(chunks)
        print(f"\n\nFINAL_RESULT: {final_result}")

        # Send Final Result to user
        args = {
            'content': final_result['content']
        }
        self.tools['AgentUserInterface__send_message_to_user'](**args)
        self.append_agent_log(
            ToolCallLog(
                tool_name       = 'AgentUserInterface__send_message_to_user',
                tool_arguments  = args,
                timestamp       = self.make_timestamp(),
                agent_id        = self.agent_id,
            )
        )

        # Return Final Result
        if final_result['type'] == "error":
            self.custom_state["running_state"] = RunningState.FAILED
        else:
            self.custom_state["running_state"] = RunningState.TERMINATED

        self.append_agent_log(
            FinalAnswerLog(
                content     = final_result['content'],
                timestamp   = self.make_timestamp(),
                agent_id    = self.agent_id
            )
        )
