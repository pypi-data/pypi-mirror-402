import asyncio
import sys

from xgae.engine.mcp_tool_box import XGAMcpToolBox
from xgae.engine.task_engine import XGATaskEngine

from xgae.utils.misc import read_file

from xgae.utils.setup_env import setup_langfuse, setup_env_logging

setup_env_logging()
langfuse = setup_langfuse()

def get_user_message(question)-> str:
    while True:
        user_message = input(f"\n💬 {question}: ")
        if user_message.lower() == 'exit' or user_message.lower() == 'quit':
            print("\n====== Extreme General Agent Engine CLI EXIT ======")
            sys.exit()

        if not user_message.strip():
            print("\nuser message is empty， input agin ！！！\n")
            continue

        return user_message

async def cli() -> None:
    await asyncio.sleep(1)
    print("\n====== Extreme General Agent Engine CLI START ======")
    user_message = input("\n💬 Start Custom MCP Server and Load User Prompt (Yes/No): ")
    tool_box = XGAMcpToolBox(custom_mcp_server_file="xga_mcp_servers.json")
    system_prompt = None
    general_tools = []
    custom_tools = []
    if user_message.lower() == 'yes':
        print(f"--- Start Custom MCP Server in custom_servers.json")
        print(f"--- Load User Prompt in example/fault_user_prompt.md")
        system_prompt = read_file("templates/example/fault_user_prompt.md")
        custom_tools = ["*"]
    else:
        print(f"--- Start General Agent Server")
        print(f"--- Load System Prompt")
        general_tools = ["*"]

    while True:
        user_message = get_user_message("Enter your task input message (or 'exit' to quit)")

        print("\n🔄 Running XGA Engine ...\n")
        engine = XGATaskEngine(tool_box=tool_box,
                               general_tools=general_tools,
                               custom_tools=custom_tools,
                               system_prompt=system_prompt)

        # Two task run in same langfuse trace
        trace_id = langfuse.trace(name="xgae_cli").trace_id
        auto_continue = True
        while auto_continue:
            auto_continue = False
            final_result = await engine.run_task_with_final_answer(
                task_input={'role': "user", 'content': user_message},
                trace_id=trace_id
            )

            if final_result["type"] == "ask":
                await asyncio.sleep(1)
                print(f"\n📌 ASK INFO: {final_result['content']}")
                user_message = get_user_message("Enter ASK information (or 'exit' to quit)")
                auto_continue = True
                continue

            await asyncio.sleep(1)
            result_prefix = "✅" if final_result["type"] == "answer" else "❌"
            print(f"\n {result_prefix} FINAL RESULT: {final_result['content']}")


def main():
    asyncio.run(cli())


if __name__ == "__main__":
    main()