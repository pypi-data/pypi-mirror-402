import asyncio

from uuid import uuid4

from xgae.utils.setup_env import setup_logging

from examples.agent.langgraph.reflection.reflection_agent import ReflectiontAgent, AgentContext


async def main():
    is_stream = True  # two mode agent experience
    task_no = 0
    user_inputs = [
        #"5+5", # For no tool call
        #"locate 10.2.3.4 fault and solution",  # For custom tool
        "locate fault and solution",   # For human append input
    ]

    for user_input in user_inputs:
        agent = ReflectiontAgent(use_prompt_rag=True)
        task_no += 1
        context: AgentContext = {
            'task_id': f"agent_task_{uuid4()}",   # can be set with request_id, must be unique
            'user_id': "agent_user_1",
            'agent_id': "agent_1",
        }

        is_resume = False
        auto_continue = True
        while auto_continue:
            if is_stream:
                print(f"*** START AGENT : RUN generate USER_INPUT={user_input}")
                async for chunk in agent.generate(user_input, context, is_resume):
                    type = chunk['type']
                    if type == "error" or type == "answer":
                        await asyncio.sleep(1)
                        print(f"FINAL_RESULT: {chunk}")
                        auto_continue = False
                    elif type == "ask":
                        print(f"ASK_USER: {chunk}")
                        user_input = "17.0.0.1"
                        is_resume = True
                        auto_continue = True
                    else:
                        print(f"RESULT_CHUNK: {chunk}")
                        auto_continue = False
            else:
                print(f"*** START AGENT : RUN generate_with_result  USER_INPUT={user_input}")
                result = await agent.generate_with_result(user_input, context, is_resume)
                await asyncio.sleep(1)
                type = result['type']
                if type == "error" or type == "answer":
                    print(f"FINAL_RESULT: {result}")
                    auto_continue = False
                elif type == "ask":
                    print(f"ASK_USER: {result}")
                    user_input = "18.0.0.1"
                    is_resume = True
                    auto_continue = True


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())