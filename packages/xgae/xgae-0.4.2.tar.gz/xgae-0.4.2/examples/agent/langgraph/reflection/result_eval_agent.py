import json
import logging
import re

from typing import Any, Dict, List, Optional

from xgae.engine.engine_base import XGATaskResult
from xgae.utils.misc import read_file
from xgae.utils.llm_client import LLMClient, LangfuseMetadata


class TaskResultEvalAgent:
    def __init__(self):
        self.model_client = LLMClient()
        self.prompt_template: str = read_file("templates/example/result_eval_template.txt")


    async def eval_result(self,
                          task_input: str,
                          task_plan: str,
                          task_result: XGATaskResult,
                          llm_messages: List[Dict[str, Any]],
                          trace_id: Optional[str] = None,
                          session_id: Optional[str] = None)-> Dict[str, Any]:
        prompt = self._build_prompt(task_input, task_plan, task_result, llm_messages)
        messages = [{"role": "user", "content": prompt}]

        langfuse_metadata = self._create_llm_langfuse_meta(trace_id, session_id)

        logging.info("TaskResultEvalAgent: LLM Eval result.....")
        response = await self.model_client.acompletion(messages, langfuse_metadata)
        response_text = await self.model_client.get_acompletion_response(response)

        cleaned_text = re.sub(r'^\s*```json|```\s*$', '', response_text, flags=re.MULTILINE).strip()
        eval_result = json.loads(cleaned_text)

        result_score = eval_result.get('task_result', {}).get('score', -1)
        plan_score = eval_result.get('task_plan', {}).get('score', -1)
        function_score = eval_result.get('function_call', {}).get('score', -1)

        logging.info(f"FINAL_RESULT_SCORE: task_result_score={result_score}, "
                     f"task_plan_score={plan_score}, function_call_score={function_score}")
        return eval_result


    def _build_prompt(self, task_input: str, task_plan: str, task_result: XGATaskResult, llm_messages: List[Dict[str, Any]])-> str:
        prompt = self.prompt_template.replace("{task_input}", task_input)
        prompt = prompt.replace("{task_result}", str(task_result))
        llm_process = ""
        function_process = ""
        llm_step = 1
        function_step = 1
        for llm_message in llm_messages:
            content = llm_message.get('content', '')
            if "tool_execution" in content:
                function_process += f"{function_step}. \n"
                tool_exec = json.loads(content)
                func_call = tool_exec['tool_execution']
                func_call.pop('xml_tag_name')
                clear_content = json.dumps(func_call, indent=2)
                function_process += clear_content
                function_process += "\n"
                function_step += 1
            else:
                llm_process += f"{llm_step}. \n"
                llm_process += content
                llm_process += "\n"
                llm_step += 1

        prompt = prompt.replace("{task_plan}", task_plan)
        prompt = prompt.replace("{llm_process}", llm_process)
        prompt = prompt.replace("{function_process}", function_process)

        return prompt


    def _create_llm_langfuse_meta(self, trace_id:str, session_id: str)-> LangfuseMetadata:
        generation_name = "xga_agent_final_result_completion"

        return LangfuseMetadata(
            generation_name     = generation_name,
            existing_trace_id   = trace_id,
            session_id          = session_id
        )



if __name__ == "__main__":
    import asyncio
    from xgae.utils.setup_env import setup_logging
    setup_logging()

    async def main():
        final_result_agent = TaskResultEvalAgent()

        task_plan = read_file("templates/example/fault_user_prompt.md")
        user_input = "locate 10.2.3.4 fault and solution"

        answer = ("Task Summary: The fault for IP 10.2.3.4 was identified as a Business Recharge Fault (Code: F01), "
                  "caused by a Phone Recharge Application Crash. The solution applied was to restart the application. "
                  "Key Deliverables: Fault diagnosis and resolution steps. Impact Achieved: Service restored.")
        task_result:XGATaskResult = {'type': "answer",  'content': answer}

        llm_messages: List[Dict[str, Any]] = [{
            'content':
                    """<function_calls> 
                        <invoke name="get_alarm_type">
                                       <parameter name="alarm_id">alm0123</parameter>
                         </invoke>
                    </function_calls>'""",
             'role': "assistant"
             },{
            'content': """{"tool_execution": {
                                "function_name": "get_alarm_type", 
                                "xml_tag_name": "get-alarm-type", 
                                "arguments": {"alarm_id": "alm0123"}, 
                                "result": {"success": true, "output": "1", "error": null}}}""",
            'role': 'assistant'
            }]

        return await final_result_agent.eval_result(user_input, task_plan, task_result, llm_messages)


    final_result = asyncio.run(main())
    final_result_json = json.dumps(final_result, ensure_ascii=False, indent=2)
    print(f"FINAL_RESULT：   {final_result_json} ")