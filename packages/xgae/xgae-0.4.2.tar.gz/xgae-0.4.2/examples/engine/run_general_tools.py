import asyncio

from xgae.engine.task_engine import XGATaskEngine
from xgae.utils.setup_env import setup_logging
from xgae.engine.mcp_tool_box import XGAMcpToolBox

setup_logging()

tool_box = XGAMcpToolBox(custom_mcp_server_file="xga_mcp_servers.json")

# Before run examples execute with 'xgatools' project: uv run xgatools

async def run_only_general_tools() -> None:
    engine = XGATaskEngine(tool_box=tool_box, general_tools=["*"], custom_tools=[])

    print("Use only general tools")
    user_input =  "Give me this week's beijing weather, and output with markdown table format"

    final_result = await engine.run_task_with_final_answer(task_input={"role": "user", "content": user_input})
    print("FINAL RESULT:", final_result)
    #print(engine.task_prompt)

# Before run this example execute: uv run example-fault-tools --alarmtype 3
async def run_general_plus_custom_tools() -> None:
    print("\n")
    print("*"*100)
    engine = XGATaskEngine(tool_box=tool_box, general_tools=["*"], custom_tools=["*"])
    print("Use external custom tools with general tools, under no custom prompt")

    # This is not a good question, just show general agent plus custom tools mode
    # If you use custom tools mainly, you should give engine 'system_prompt'
    user_input = "get 10.0.0.1 fault cause"
    final_result = await engine.run_task_with_final_answer(task_input={"role": "user", "content": user_input})
    print("FINAL RESULT:", final_result)
    #print(engine.task_prompt)

async def main() -> None:
    await run_only_general_tools()

    #await run_general_plus_custom_tools()

asyncio.run(main())