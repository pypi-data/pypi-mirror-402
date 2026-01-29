import logging
from typing import Any, Optional, Callable, Literal, Dict, List
from typing_extensions import override

from xgae.engine.engine_base import XGAToolBox
from xgae.engine.task_engine import XGATaskEngine
from xgae.engine.prompt_builder import XGAPromptBuilder
from xgae.utils.llm_client import LLMConfig


class ARETaskEngine(XGATaskEngine):
    def __init__(self,
                 agent: Any,
                 agent_id: str,
                 max_auto_run: int,
                 llm_config: Optional[LLMConfig] = None,
                 tool_box: Optional[XGAToolBox] = None,
                 prompt_builder: Optional[XGAPromptBuilder] = None,
                 pre_run_task_fn : Callable[[Any, int, List[Dict[str, Any]]], Any] = None,
                 post_run_task_fn : Callable[[Any, int, Dict[str, Any]], Any] = None,
                 terminate_task_fn : Callable[[Any, int], bool] = None,
                ):
        super().__init__(agent_id       = agent_id,
                         general_tools  = [],
                         custom_tools   = ["*"],
                         max_auto_run   = max_auto_run,
                         llm_config     = llm_config,
                         tool_box       = tool_box,
                         prompt_builder = prompt_builder,
                         )
        self.agent = agent
        self.pre_run_task_fn = pre_run_task_fn
        self.post_run_task_fn = post_run_task_fn
        self.terminate_task_fn = terminate_task_fn


    @override
    def running_task_checkpoint(self,
                                task_state: Literal["before_completion", "after_completion", "termination_check"],
                                iterations: int,
                                llm_messages: List[Dict[str, Any]] = None,
                                llm_response: Dict[str, Any] = None
                                )-> bool:
        is_continue_task = True

        if task_state == "before_completion" and self.pre_run_task_fn:
            self.pre_run_task_fn(self.agent, iterations, llm_messages)
        elif task_state == "after_completion" and self.post_run_task_fn:
            self.post_run_task_fn(self.agent, iterations, llm_response)
        elif task_state == "termination_check":
            if self.terminate_task:
                logging.warning(f"running_task_checkpoint: ⚠️ TASK: {self.task_id} STOP RUNNING for STOP Command !")

            if self.terminate_task_fn:
                is_terminate = self.terminate_task_fn(self.agent, iterations) if self.terminate_task_fn  else False
                if is_terminate:
                    logging.warning(f"running_task_checkpoint: ⚠️ TASK: {self.task_id} STOP RUNNING for Termination Function !")
                    self.stop_task()

            is_continue_task = not self.terminate_task

        return is_continue_task



if __name__ == "__main__":
    import asyncio
    import os
    from xgae.utils.misc import read_file
    from xgae.utils.setup_env import setup_logging
    from xgae.engine.mcp_tool_box import XGAMcpToolBox
    from xgae.engine.prompt_builder import XGAPromptBuilder

    setup_logging()

    def pre_run_task(agent, iterations:int, llm_messages: List[Dict[str, Any]]):
        prompt = "\n\n".join([f"{key}: {value}" for d in llm_messages for key, value in d.items()]) if llm_messages else ""
        logging.info(f"pre_run_task: iterations={iterations}, prompt: \n{prompt}\n")


    def post_run_task(agent, iterations: int, llm_response: Dict[str, Any]):
        logging.info(f"post_run_task: iterations={iterations}, prompt: \n{llm_response}\n")


    def terminate_task(agent, iterations: int) -> bool:
        logging.info(f"terminate_task: iterations={iterations}")
        return iterations > 8 # can test terminate by > 3


    async def main():
        # Before Run Exec: uv run example-fault-tools
        # LLAMA_API_KEY , LLAMA_API_BASE
        tool_box = XGAMcpToolBox(custom_mcp_server_file="xga_mcp_servers.json")
        system_prompt = read_file("templates/example/fault_user_prompt.md")
        prompt_builder = XGAPromptBuilder(system_prompt)
        llm_config = LLMConfig(
            model            = "openai/qwen-plus",
            api_key          = os.getenv('LLAMA_API_KEY') ,
            api_base         = os.getenv('LLAMA_API_BASE'),
            stream           =True,
            enable_thinking  = False,
        )

        engine =  ARETaskEngine(
            agent               = "AREAgent", # Just for test,ARE use real Agent Object
            agent_id            = "agent_1",
            max_auto_run        = 15,
            llm_config          = llm_config,
            tool_box            = tool_box,
            prompt_builder      = prompt_builder,
            pre_run_task_fn     = pre_run_task,
            post_run_task_fn    = post_run_task,
            terminate_task_fn   = terminate_task
        )

        user_input = "locate 10.0.0.1 fault and solution"
        chunks = []
        async for chunk in engine.run_task(task_input={"role": "user", "content": user_input}):
            chunks.append(chunk)
            print(chunk)

        final_result = engine.parse_final_result(chunks)
        print(f"\n\nFINAL_RESULT: {final_result}")


    asyncio.run(main())